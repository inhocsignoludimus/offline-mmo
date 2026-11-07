'use strict';
// =====================================================================
// systems/sim.js — jogadores simulados: entram e saem do "servidor", andam
// pela cidade, conversam (local, global, guilda, sussurro), respondem ao
// jogador, recrutam para guildas, declaram guerras e chamam raids.
// Nomes e guildas: data/names (Ludimus). Frases: data/chat.
// =====================================================================
const rnd = a => a[Math.floor(Math.random() * a.length)];
const chance = p => Math.random() < p;
const between = (a, b) => a + Math.random() * (b - a);

// personalidade mais provável para cada estilo de nome
const PERS_DO_ESTILO = {
  gamer: ['pvper', 'pvper', 'farmador', 'troll'],
  fantasia: ['farmador', 'novato', 'comerciante', 'pvper'],
  rp_historico: ['roleplayer', 'roleplayer', 'roleplayer', 'comerciante'],
  br_zoeira: ['troll', 'troll', 'novato', 'pvper'],
  simples: ['novato', 'farmador', 'comerciante', 'novato'],
  numero: ['farmador', 'pvper', 'troll', 'novato'],
};
// que guilda combina com que personalidade
const GUILDA_COMBINA = { rp: ['roleplayer', 'comerciante'], pvp: ['pvper', 'troll', 'farmador'], trade: ['comerciante', 'farmador'], farm: ['farmador', 'novato'] };

// visuais com as camadas do TCoM
const VISUAIS_M = [
  () => [rnd(['cloth_pants', 'calca_branca']), rnd(['cloth_sandals', 'leather_boots']), rnd(['aldeao_tunica1', 'aldeao_tunica2', 'cloth_shirt', 'ferreiro_tunica']), rnd(['male_head1', 'male_head2']), ...(chance(0.3) ? ['leather_hood'] : []), ...(chance(0.5) ? [rnd(['dagger', 'hand_axe', 'martelo'])] : [])],
  () => ['chain_greaves', rnd(['chain_boots', 'leather_boots']), rnd(['loriga', 'lorigao', 'lamelar', 'gambesao', 'jaque_couro', 'chain_cuirass', 'leather_armor', 'cazagante']), rnd(['chain_gloves', 'leather_gloves']), rnd(['male_head1', 'male_head2']), rnd(['elmo_nasal', 'chain_coif', 'elmo_pontudo', 'elmo_grande', 'elmo_rosto']), rnd(['longsword', 'mace', 'hand_axe', 'lanca', 'infantry_axe']), rnd(['shield', 'buckler', 'escudo_redondo'])],
  () => ['chain_greaves', 'chain_boots', 'chain_gloves', rnd(['armadura_templario', 'armadura_cruzado', 'armadura_sargento']), rnd(['male_head1', 'male_head2']), rnd(['elmo_nasal', 'chain_coif']), 'longsword', 'escudo_cruz'],
  () => ['beduino_saia', 'beduino_veste', 'beduino_mangas', 'cloth_sandals', rnd(['male_head1', 'male_head2']), 'turbante', rnd(['dagger', 'lanca', 'hand_axe', 'longsword']), ...(chance(0.5) ? ['escudo_redondo'] : [])],
  () => ['cloth_pants', 'cloth_sandals', 'habito_peregrino', rnd(['male_head1', 'male_head2'])],
  () => ['beduino_saia', 'leather_boots', rnd(['couraca_turca', 'gibao_egipcio']), 'beduino_mangas', rnd(['male_head1', 'male_head2']), rnd(['elmo_pontudo', 'keffiyeh', 'turbante']), rnd(['arco', 'besta', 'longsword'])],
];
const VISUAIS_F = [() => [rnd(['clothes', 'aldea_roupa2', 'aldea_roupa2', 'habito']), 'head_long']];

const COR_NOME = { inocente: '#6ab0ff', criminoso: '#a0a0a0', assassino: '#ff5a4a', aliado: '#5ee07a', inimigo: '#ffa040' };

const Sim = {
  sims: [], guilds: [], wars: [], raids: [], invites: {}, t: 0, nextGlobal: 8, nextLogin: 25, nextGuild: 90,
  // quantos andam na cidade com o jogador (o resto está online em outros lugares, só no chat)
  NEAR_START: 7, NEAR_MAX: 9,
  init(data, map) {
    this.map = map;
    this.guilds = data.guilds.guilds.map(g => ({ ...g, members: [] }));
    for (const p of data.players.players) {
      const pers = rnd(PERS_DO_ESTILO[p.style] || ['novato']);
      const s = { name: p.name, sex: p.sex === 'f' ? 'f' : 'm', style: p.style, pers, guild: null, online: false, near: false, actor: null, rel: 'neutro', murderer: false };
      // 60% em guilda, preferindo a que combina com a personalidade
      if (chance(0.6)) {
        const pref = this.guilds.filter(g => (GUILDA_COMBINA[g.style] || []).includes(pers));
        s.guild = rnd(pref.length && chance(0.8) ? pref : this.guilds); s.guild.members.push(s);
      }
      // sem PvP: ninguém é assassino
      this.sims.push(s);
    }
    // guerras iniciais entre guildas de caos e de ordem
    const caos = this.guilds.filter(g => g.align === 'caos'), ordem = this.guilds.filter(g => g.align === 'ordem');
    for (let k = 0; k < 2; k++) { const a = rnd(caos), b = rnd(ordem); if (a && b && !this.atWar(a, b)) this.wars.push({ a, b }); }
    // começa com uns 40 online, 14 deles na cidade
    const sh = this.sims.slice().sort(() => Math.random() - 0.5);
    sh.slice(0, 40).forEach((s, i) => this.login(s, i < this.NEAR_START, true));
  },
  online() { return this.sims.filter(s => s.online); },
  // os jogadores simulados só andam na vila; fora dela continuam online, no chat
  leaveTown() { for (const s of this.near()) { s.near = false; s.actor = null; } },
  enterTown() { const on = this.online().filter(s => !s.near).sort(() => Math.random() - 0.5); on.slice(0, this.NEAR_START).forEach(s => { s.online = false; this.login(s, true, true); }); },
  near() { return this.sims.filter(s => s.near); },
  atWar(a, b) { return this.wars.some(w => (w.a === a && w.b === b) || (w.a === b && w.b === a)); },
  byName(n) { n = n.toLowerCase(); return this.sims.find(s => s.name.toLowerCase() === n) || this.sims.find(s => s.name.toLowerCase().startsWith(n)); },

  login(s, near, quiet) {
    s.online = true; s.near = near; s.where = rnd(Chat.places);
    if (near) {
      const ap = { sexo: s.sex, layers: (s.sex === 'f' ? rnd(VISUAIS_F) : rnd(VISUAIS_M))() };
      const [x, y] = this.map.randomFree(Math.random, Game.townCenter, 14);
      s.actor = new Actor({ x, y, ap, name: s.name, tag: s.guild ? s.guild.tag : '', kind: 'sim', speed: between(2.9, 3.8), dir: Math.floor(Math.random() * 8) });
      s.actor.sim = s; s.brain = { state: 'idle', until: this.t + between(1, 6) };
      this.color(s);
      Game.actors.push(s.actor);
      if (!quiet && chance(0.3)) setTimeout(() => this.say(s, 'greet'), between(1500, 5000));
    }
  },
  logout(s) {
    if (s.near && chance(0.3)) this.say(s, 'bye');
    const go = () => { s.online = false; s.near = false; if (s.actor) { Game.actors.splice(Game.actors.indexOf(s.actor), 1); s.actor = null; } };
    s.near ? setTimeout(go, 1800) : go();
  },
  color(s) {
    if (!s.actor) return;
    const pg = Game.player.guild;
    let c = COR_NOME.inocente;
    if (pg && s.guild === pg) c = COR_NOME.aliado;
    s.actor.nameColor = c;
  },
  recolorAll() { for (const s of this.sims) this.color(s); },

  // ------------------------------------------------------------------
  // falas
  // ------------------------------------------------------------------
  vars(s, extra) {
    const others = this.online().filter(o => o !== s);
    return { player: Game.player.name, name: s.name, target: (rnd(others) || s).name, guild: s.guild ? s.guild.name : 'Sem Guilda', tag: s.guild ? s.guild.tag : '', ...extra };
  },
  // canal real da fala, ou null se o jogador não teria como ver
  say(s, ctx, extra, forceCh) {
    if (!s.online) return false;
    const r = Chat.pick(s.pers, ctx, this.vars(s, extra)); if (!r) return false;
    let ch = forceCh || r.ch;
    if (ch === 'local' && !s.near) ch = 'global';
    if (ch === 'guild' && !(Game.player.guild && Game.player.guild === s.guild)) ch = s.near ? 'local' : 'global';
    if (ch === 'party') ch = s.near ? 'local' : 'global';
    if (ch === 'whisper' && !(extra && extra.target === Game.player.name)) ch = s.near ? 'local' : 'global';
    this.emit(s, ch, r.text);
    return true;
  },
  emit(s, ch, text) {
    const who = s.guild && ch !== 'guild' ? `${s.name} [${s.guild.tag}]` : s.name;
    Journal.add(ch, who, text);
    if (ch === 'local' && s.actor) s.actor.say = { text, until: Game.now + 2800 + text.length * 55 };
  },
  // escolhe alguém online (perto ou longe) que tenha frase para o contexto
  speaker(ctx, filter = () => true) {
    const c = this.online().filter(s => Chat.has(s.pers, ctx) && filter(s));
    return c.length ? rnd(c) : null;
  },

  // ------------------------------------------------------------------
  // o jogador falou
  // ------------------------------------------------------------------
  hear(text, ch, whisperTo) {
    const low = text.toLowerCase();
    const greet = /\b(oi+|ol[aá]|eae|e a[ií]|salve|bom dia|boa (tarde|noite)|hail|hi|hello|hey)\b/.test(low);
    const ask = /\?|\b(como|onde|algu[eé]m|quem|qual|ajuda|help)\b/.test(low);
    const rude = /\b(noob|lixo|merda|idiota|burro|otario|otário|lammer|lamer|fdp)\b/.test(low);
    const trade = /\b(wts|wtb|vendo|compro|troco|pre[cç]o)\b/.test(low);
    const lfg = /\b(lfg|grupo|party|pt|raid|bora|vamos)\b/.test(low);
    const thanks = /\b(vlw|valeu|obrigad[oa]|brigad[oa]|thx|ty)\b/.test(low);
    const relCtx = s => s.rel === 'amigo' ? 'reply_friend' : s.rel === 'inimigo' ? 'reply_enemy' : 'reply_neutral';
    const later = (fn, a = 900, b = 3200) => setTimeout(fn, between(a, b));

    if (whisperTo) {
      const s = this.byName(whisperTo);
      if (!s || !s.online) { Journal.add('system', '', `${whisperTo} não está online.`); return; }
      if (greet || thanks) s.rel = s.rel === 'inimigo' ? 'neutro' : 'amigo';
      if (rude) s.rel = 'inimigo';
      const ctx = rude ? 'reply_enemy' : ask && Chat.has(s.pers, 'help_give') ? 'help_give' : greet && chance(0.5) ? 'greet' : relCtx(s);
      later(() => this.say(s, ctx, { target: Game.player.name }, 'whisper'), 1500, 5000);
      return;
    }
    if (ch === 'guild') {
      const g = Game.player.guild; if (!g) return;
      const m = g.members.filter(s => s.online);
      if (m.length && chance(0.8)) { const s = rnd(m); later(() => this.say(s, greet ? 'greet' : lfg ? 'raid_call' : ask ? 'help_give' : 'reply_friend', { target: Game.player.name }, 'guild')); }
      return;
    }
    // local: quem está perto e ouviu
    const P = Game.player.actor;
    const ears = this.near().filter(s => Math.hypot(s.actor.x - P.x, s.actor.y - P.y) < (ch === 'global' ? 999 : 9));
    const pool = ch === 'global' ? this.online() : ears;
    const named = pool.filter(s => low.includes(s.name.toLowerCase()));
    let n = named.length ? 1 : ch === 'global' ? (chance(0.6) ? 1 : 0) + (chance(0.25) ? 1 : 0) : Math.min(pool.length, (chance(0.7) ? 1 : 0) + (chance(0.3) ? 1 : 0));
    const used = new Set();
    for (let k = 0; k < n; k++) {
      const cands = (named.length ? named : pool).filter(s => !used.has(s));
      let s, ctx;
      if (rude) { s = rnd(cands); if (s) s.rel = 'inimigo'; ctx = 'reply_enemy'; }
      else if (trade) { s = cands.find(c => c.pers === 'comerciante') || rnd(cands); ctx = 'trade_haggle'; }
      else if (ask) { s = cands.find(c => Chat.has(c.pers, 'help_give')) || rnd(cands); ctx = 'help_give'; }
      else if (lfg) { s = rnd(cands); ctx = 'lfg'; }
      else if (greet) { s = rnd(cands); ctx = chance(0.5) ? 'greet' : 'reply_friend'; }
      else if (thanks) { s = rnd(cands); ctx = 'reply_friend'; }
      else { s = rnd(cands); ctx = s ? relCtx(s) : null; }
      if (!s) break;
      used.add(s);
      if (!Chat.has(s.pers, ctx)) ctx = relCtx(s);
      if (s.near && s.actor) this.face(s.actor, P);
      later(() => this.say(s, ctx, { target: Game.player.name }, ch === 'global' ? 'global' : null), 900 + k * 1600, 3000 + k * 2200);
    }
  },
  face(a, b) { a.dir = direcaoDoAngulo(Math.atan2(b.y - a.y, b.x - a.x)); },

  // aceitar convite de guilda
  accept() {
    const inv = this.invites.last;
    if (!inv || Game.now - inv.at > 120000) { Journal.add('system', '', 'Nenhum convite de guilda pendente.'); return; }
    Game.player.guild = inv.guild; inv.guild.members.push(Game.playerSim);
    Journal.add('system', '', `Você entrou na guilda ${inv.guild.name} [${inv.guild.tag}].`);
    HUD.toast(`Bem-vindo à ${inv.guild.name}!`); this.invites.last = null; this.recolorAll();
    const m = inv.guild.members.filter(s => s.online && s !== Game.playerSim);
    m.slice(0, 3).forEach((s, i) => setTimeout(() => this.say(s, 'greet', { target: Game.player.name }, 'guild'), 1500 + i * 1800));
  },
  leave() {
    const g = Game.player.guild; if (!g) { Journal.add('system', '', 'Você não está em uma guilda.'); return; }
    g.members.splice(g.members.indexOf(Game.playerSim), 1); Game.player.guild = null;
    Journal.add('system', '', `Você saiu da guilda ${g.name}.`); this.recolorAll();
  },

  // ------------------------------------------------------------------
  // atualização
  // ------------------------------------------------------------------
  update(dt) {
    this.t += dt;
    for (const s of this.near()) this.brain(s, dt);
    if (this.t > this.nextGlobal) { this.nextGlobal = this.t + between(14, 32); this.globalEvent(); }
    if (this.t > this.nextLogin) { this.nextLogin = this.t + between(12, 35); this.churn(); }
    if (this.t > this.nextGuild) { this.nextGuild = this.t + between(120, 260); this.guildEvent(); }
    for (const r of this.raids.slice()) if (this.t > r.end) {
      this.raids.splice(this.raids.indexOf(r), 1);
      const s = rnd(r.guild.members.filter(m => m.online && m !== Game.playerSim)); if (!s) continue;
      const win = chance(0.55);
      this.say(s, win ? 'raid_win' : 'raid_wipe', { boss: r.boss }, Game.player.guild === r.guild ? 'guild' : 'global');
      if (win && chance(0.6)) setTimeout(() => { const o = rnd(r.guild.members.filter(m => m.online)); o && this.say(o, 'loot_rare', null, Game.player.guild === r.guild ? 'guild' : 'global'); }, 4000);
    }
  },
  brain(s, dt) {
    const a = s.actor, b = s.brain, P = Game.player.actor;
    if (a.path) return;
    if (this.t < b.until) return;
    const r = Math.random();
    if (r < 0.5) { // passear
      const followMe = World.safe(P.x, P.y) && chance(0.25);
      const [x, y] = this.map.randomFree(Math.random, followMe ? [P.x, P.y] : Game.townCenter, followMe ? 5 : 16);
      a.moveTo(this.map, x, y); b.until = this.t + between(2, 8);
    } else if (r < 0.62 && a.ap.layers.some(l => TCOM.slot[l] === 'main')) { // treinar golpes
      a.setAnim('swing'); b.until = this.t + between(0.6, 1.2);
    } else { // ficar parado e às vezes falar
      b.until = this.t + between(4, 14);
      if (chance(0.07)) {
        const ctx = rnd(s.pers === 'comerciante' ? ['trade_sell', 'trade_buy', 'idle'] : ['idle', 'idle', 'lfg', 'brag', 'help_ask', 'complain_server']);
        this.say(s, ctx, null, 'local');
      }
    }
    // alguém perto puxa conversa com o jogador
    if (chance(0.006) && Math.hypot(a.x - P.x, a.y - P.y) < 6) { this.face(a, P); this.say(s, chance(0.5) ? 'greet' : 'help_ask', { target: Game.player.name }, 'local'); }
  },
  globalEvent() {
    const ctx = rnd(['trade_sell', 'trade_sell', 'trade_buy', 'lfg', 'lfg', 'complain_server', 'loot_rare', 'death_self', 'brag', 'guild_recruit', 'help_ask', 'lfg']);
    const s = this.speaker(ctx, x => !x.near || ctx === 'guild_recruit'); if (!s) return;
    if (ctx === 'guild_recruit') {
      if (!s.guild || Game.player.guild) return;
      this.say(s, ctx, null, 'global');
      if (chance(0.35)) setTimeout(() => {
        if (Game.player.guild) return;
        this.invites.last = { guild: s.guild, from: s, at: Game.now };
        Journal.add('whisper', s.name, `${Game.player.name}, quer entrar na ${s.guild.name}?`);
        Prompt.ask(`${s.name} convida você para a guilda ${s.guild.name} [${s.guild.tag}].`, [['Aceitar', () => this.accept()], ['Recusar', () => { this.invites.last = null; }]]);
      }, 3500);
      return;
    }
    this.say(s, ctx, null, 'global');
    // às vezes alguém responde no global
    if (chance(0.15)) setTimeout(() => { const o = this.speaker('reply_neutral', x => x !== s); o && this.say(o, rnd(['reply_neutral', 'reply_friend', 'reply_enemy']), { target: s.name }, 'global'); }, between(2000, 6000));
    // conversa da própria guilda do jogador
    const pg = Game.player.guild;
    if (pg && chance(0.25)) { const m = this.speaker(rnd(['idle', 'lfg', 'brag', 'help_ask', 'reply_friend']), x => x.guild === pg); m && setTimeout(() => this.say(m, rnd(['idle', 'lfg', 'brag', 'help_ask']), null, 'guild'), 2500); }
  },
  churn() {
    const on = this.online(), off = this.sims.filter(s => !s.online);
    if (on.length > 30 && chance(0.6)) this.logout(rnd(on));
    if (off.length && on.length < 55 && chance(0.7)) {
      const s = rnd(off), near = this.near().length < this.NEAR_MAX && chance(0.4);
      this.login(s, near);
      if (!near && chance(0.3)) setTimeout(() => this.say(s, 'greet', null, 'global'), 1500);
    }
  },
  guildEvent() {
    const r = Math.random();
    if (r < 0.35) { // declaração de guerra
      const a = rnd(this.guilds.filter(g => g.align !== 'ordem')), b = rnd(this.guilds.filter(g => g !== a && g.align !== a.align));
      if (!a || !b || this.atWar(a, b)) return;
      const s = rnd(a.members.filter(m => m.online && m !== Game.playerSim)); if (!s) return;
      this.wars.push({ a, b }); if (this.wars.length > 4) this.wars.shift();
      this.say(s, 'guild_war_declare', { target: b.name, guild: a.name }, 'global');
      Journal.add('system', '', `A guilda ${a.name} [${a.tag}] declarou guerra à ${b.name} [${b.tag}].`);
      this.recolorAll();
      setTimeout(() => { const o = rnd(b.members.filter(m => m.online && m !== Game.playerSim)); o && this.say(o, 'guild_war_taunt', { target: a.name }, 'global'); }, between(3000, 9000));
    } else if (r < 0.65) { // provocação de uma guerra já em curso
      const w = rnd(this.wars); if (!w) return;
      const g = chance(0.5) ? w.a : w.b, o = g === w.a ? w.b : w.a;
      const s = rnd(g.members.filter(m => m.online && m !== Game.playerSim)); s && this.say(s, 'guild_war_taunt', { target: o.name }, 'global');
    } else { // raid
      const g = rnd(this.guilds.filter(x => x.members.some(m => m.online)));
      const s = g && rnd(g.members.filter(m => m.online && m !== Game.playerSim)); if (!s) return;
      const boss = rnd(Chat.bosses);
      this.say(s, 'raid_call', { boss }, Game.player.guild === g ? 'guild' : 'global');
      this.raids.push({ guild: g, boss, end: this.t + between(90, 240) });
    }
  },
};
