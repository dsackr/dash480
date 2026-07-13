/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const L = globalThis, J = L.ShadowRoot && (L.ShadyCSS === void 0 || L.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, K = Symbol(), Q = /* @__PURE__ */ new WeakMap();
let $e = class {
  constructor(e, t, s) {
    if (this._$cssResult$ = !0, s !== K) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (J && e === void 0) {
      const s = t !== void 0 && t.length === 1;
      s && (e = Q.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), s && Q.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Ae = (i) => new $e(typeof i == "string" ? i : i + "", void 0, K), fe = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new $e(t, i, K);
}, Pe = (i, e) => {
  if (J) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const s = document.createElement("style"), r = L.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = t.cssText, i.appendChild(s);
  }
}, ee = J ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const s of e.cssRules) t += s.cssText;
  return Ae(t);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Ee, defineProperty: ke, getOwnPropertyDescriptor: Se, getOwnPropertyNames: Ce, getOwnPropertySymbols: Oe, getPrototypeOf: Te } = Object, m = globalThis, te = m.trustedTypes, Ne = te ? te.emptyScript : "", V = m.reactiveElementPolyfillSupport, N = (i, e) => i, F = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? Ne : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, e) {
  let t = i;
  switch (e) {
    case Boolean:
      t = i !== null;
      break;
    case Number:
      t = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(i);
      } catch {
        t = null;
      }
  }
  return t;
} }, X = (i, e) => !Ee(i, e), ie = { attribute: !0, type: String, converter: F, reflect: !1, useDefault: !1, hasChanged: X };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), m.litPropertyMetadata ?? (m.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let k = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = ie) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(e, s, t);
      r !== void 0 && ke(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, s) {
    const { get: r, set: o } = Se(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: r, set(n) {
      const l = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(e, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ie;
  }
  static _$Ei() {
    if (this.hasOwnProperty(N("elementProperties"))) return;
    const e = Te(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(N("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(N("properties"))) {
      const t = this.properties, s = [...Ce(t), ...Oe(t)];
      for (const r of s) this.createProperty(r, t[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [s, r] of t) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, s] of this.elementProperties) {
      const r = this._$Eu(t, s);
      r !== void 0 && this._$Eh.set(r, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const s = new Set(e.flat(1 / 0).reverse());
      for (const r of s) t.unshift(ee(r));
    } else e !== void 0 && t.push(ee(e));
    return t;
  }
  static _$Eu(e, t) {
    const s = t.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var e;
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (e = this.constructor.l) == null || e.forEach((t) => t(this));
  }
  addController(e) {
    var t;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(e), this.renderRoot !== void 0 && this.isConnected && ((t = e.hostConnected) == null || t.call(e));
  }
  removeController(e) {
    var t;
    (t = this._$EO) == null || t.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const s of t.keys()) this.hasOwnProperty(s) && (e.set(s, this[s]), delete this[s]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return Pe(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((t) => {
      var s;
      return (s = t.hostConnected) == null ? void 0 : s.call(t);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((t) => {
      var s;
      return (s = t.hostDisconnected) == null ? void 0 : s.call(t);
    });
  }
  attributeChangedCallback(e, t, s) {
    this._$AK(e, s);
  }
  _$ET(e, t) {
    var o;
    const s = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, s);
    if (r !== void 0 && s.reflect === !0) {
      const n = (((o = s.converter) == null ? void 0 : o.toAttribute) !== void 0 ? s.converter : F).toAttribute(t, s.type);
      this._$Em = e, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var o, n;
    const s = this.constructor, r = s._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const l = s.getPropertyOptions(r), a = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((o = l.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? l.converter : F;
      this._$Em = r;
      const p = a.fromAttribute(t, l.type);
      this[r] = p ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? p, this._$Em = null;
    }
  }
  requestUpdate(e, t, s, r = !1, o) {
    var n;
    if (e !== void 0) {
      const l = this.constructor;
      if (r === !1 && (o = this[e]), s ?? (s = l.getPropertyOptions(e)), !((s.hasChanged ?? X)(o, t) || s.useDefault && s.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(e)) && !this.hasAttribute(l._$Eu(e, s)))) return;
      this.C(e, t, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: s, reflect: r, wrapped: o }, n) {
    s && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || s || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var s;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [o, n] of this._$Ep) this[o] = n;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [o, n] of r) {
        const { wrapped: l } = n, a = this[o];
        l !== !0 || this._$AL.has(o) || a === void 0 || this.C(o, void 0, n, a);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (s = this._$EO) == null || s.forEach((r) => {
        var o;
        return (o = r.hostUpdate) == null ? void 0 : o.call(r);
      }), this.update(t)) : this._$EM();
    } catch (r) {
      throw e = !1, this._$EM(), r;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    var t;
    (t = this._$EO) == null || t.forEach((s) => {
      var r;
      return (r = s.hostUpdated) == null ? void 0 : r.call(s);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t) => this._$ET(t, this[t]))), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
k.elementStyles = [], k.shadowRootOptions = { mode: "open" }, k[N("elementProperties")] = /* @__PURE__ */ new Map(), k[N("finalized")] = /* @__PURE__ */ new Map(), V == null || V({ ReactiveElement: k }), (m.reactiveElementVersions ?? (m.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const M = globalThis, se = (i) => i, B = M.trustedTypes, re = B ? B.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, ye = "$lit$", v = `lit$${Math.random().toFixed(9).slice(2)}$`, ve = "?" + v, Me = `<${ve}>`, P = document, U = () => P.createComment(""), R = (i) => i === null || typeof i != "object" && typeof i != "function", Y = Array.isArray, Ue = (i) => Y(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", W = `[ 	
\f\r]`, T = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ne = /-->/g, oe = />/g, w = RegExp(`>|${W}(?:([^\\s"'>=/]+)(${W}*=${W}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), ae = /'/g, le = /"/g, me = /^(?:script|style|textarea|title)$/i, Re = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), d = Re(1), C = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), he = /* @__PURE__ */ new WeakMap(), x = P.createTreeWalker(P, 129);
function be(i, e) {
  if (!Y(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return re !== void 0 ? re.createHTML(e) : e;
}
const He = (i, e) => {
  const t = i.length - 1, s = [];
  let r, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = T;
  for (let l = 0; l < t; l++) {
    const a = i[l];
    let p, u, h = -1, f = 0;
    for (; f < a.length && (n.lastIndex = f, u = n.exec(a), u !== null); ) f = n.lastIndex, n === T ? u[1] === "!--" ? n = ne : u[1] !== void 0 ? n = oe : u[2] !== void 0 ? (me.test(u[2]) && (r = RegExp("</" + u[2], "g")), n = w) : u[3] !== void 0 && (n = w) : n === w ? u[0] === ">" ? (n = r ?? T, h = -1) : u[1] === void 0 ? h = -2 : (h = n.lastIndex - u[2].length, p = u[1], n = u[3] === void 0 ? w : u[3] === '"' ? le : ae) : n === le || n === ae ? n = w : n === ne || n === oe ? n = T : (n = w, r = void 0);
    const y = n === w && i[l + 1].startsWith("/>") ? " " : "";
    o += n === T ? a + Me : h >= 0 ? (s.push(p), a.slice(0, h) + ye + a.slice(h) + v + y) : a + v + (h === -2 ? l : y);
  }
  return [be(i, o + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), s];
};
class H {
  constructor({ strings: e, _$litType$: t }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const l = e.length - 1, a = this.parts, [p, u] = He(e, t);
    if (this.el = H.createElement(p, s), x.currentNode = this.el.content, t === 2 || t === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (r = x.nextNode()) !== null && a.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const h of r.getAttributeNames()) if (h.endsWith(ye)) {
          const f = u[n++], y = r.getAttribute(h).split(v), j = /([.?@])?(.*)/.exec(f);
          a.push({ type: 1, index: o, name: j[2], strings: y, ctor: j[1] === "." ? Ie : j[1] === "?" ? ze : j[1] === "@" ? je : G }), r.removeAttribute(h);
        } else h.startsWith(v) && (a.push({ type: 6, index: o }), r.removeAttribute(h));
        if (me.test(r.tagName)) {
          const h = r.textContent.split(v), f = h.length - 1;
          if (f > 0) {
            r.textContent = B ? B.emptyScript : "";
            for (let y = 0; y < f; y++) r.append(h[y], U()), x.nextNode(), a.push({ type: 2, index: ++o });
            r.append(h[f], U());
          }
        }
      } else if (r.nodeType === 8) if (r.data === ve) a.push({ type: 2, index: o });
      else {
        let h = -1;
        for (; (h = r.data.indexOf(v, h + 1)) !== -1; ) a.push({ type: 7, index: o }), h += v.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const s = P.createElement("template");
    return s.innerHTML = e, s;
  }
}
function O(i, e, t = i, s) {
  var n, l;
  if (e === C) return e;
  let r = s !== void 0 ? (n = t._$Co) == null ? void 0 : n[s] : t._$Cl;
  const o = R(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((l = r == null ? void 0 : r._$AO) == null || l.call(r, !1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, t, s)), s !== void 0 ? (t._$Co ?? (t._$Co = []))[s] = r : t._$Cl = r), r !== void 0 && (e = O(i, r._$AS(i, e.values), r, s)), e;
}
class De {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: s } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? P).importNode(t, !0);
    x.currentNode = r;
    let o = x.nextNode(), n = 0, l = 0, a = s[0];
    for (; a !== void 0; ) {
      if (n === a.index) {
        let p;
        a.type === 2 ? p = new D(o, o.nextSibling, this, e) : a.type === 1 ? p = new a.ctor(o, a.name, a.strings, this, e) : a.type === 6 && (p = new Le(o, this, e)), this._$AV.push(p), a = s[++l];
      }
      n !== (a == null ? void 0 : a.index) && (o = x.nextNode(), n++);
    }
    return x.currentNode = P, r;
  }
  p(e) {
    let t = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(e, s, t), t += s.strings.length - 2) : s._$AI(e[t])), t++;
  }
}
class D {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, s, r) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = s, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && (e == null ? void 0 : e.nodeType) === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = O(this, e, t), R(e) ? e === c || e == null || e === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : e !== this._$AH && e !== C && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Ue(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== c && R(this._$AH) ? this._$AA.nextSibling.data = e : this.T(P.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var o;
    const { values: t, _$litType$: s } = e, r = typeof s == "number" ? this._$AC(e) : (s.el === void 0 && (s.el = H.createElement(be(s.h, s.h[0]), this.options)), s);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === r) this._$AH.p(t);
    else {
      const n = new De(r, this), l = n.u(this.options);
      n.p(t), this.T(l), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = he.get(e.strings);
    return t === void 0 && he.set(e.strings, t = new H(e)), t;
  }
  k(e) {
    Y(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let s, r = 0;
    for (const o of e) r === t.length ? t.push(s = new D(this.O(U()), this.O(U()), this, this.options)) : s = t[r], s._$AI(o), r++;
    r < t.length && (this._$AR(s && s._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var s;
    for ((s = this._$AP) == null ? void 0 : s.call(this, !1, !0, t); e !== this._$AB; ) {
      const r = se(e).nextSibling;
      se(e).remove(), e = r;
    }
  }
  setConnected(e) {
    var t;
    this._$AM === void 0 && (this._$Cv = e, (t = this._$AP) == null || t.call(this, e));
  }
}
class G {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, s, r, o) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = o, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = c;
  }
  _$AI(e, t = this, s, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = O(this, e, t, 0), n = !R(e) || e !== this._$AH && e !== C, n && (this._$AH = e);
    else {
      const l = e;
      let a, p;
      for (e = o[0], a = 0; a < o.length - 1; a++) p = O(this, l[s + a], t, a), p === C && (p = this._$AH[a]), n || (n = !R(p) || p !== this._$AH[a]), p === c ? e = c : e !== c && (e += (p ?? "") + o[a + 1]), this._$AH[a] = p;
    }
    n && !r && this.j(e);
  }
  j(e) {
    e === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Ie extends G {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === c ? void 0 : e;
  }
}
class ze extends G {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== c);
  }
}
class je extends G {
  constructor(e, t, s, r, o) {
    super(e, t, s, r, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = O(this, e, t, 0) ?? c) === C) return;
    const s = this._$AH, r = e === c && s !== c || e.capture !== s.capture || e.once !== s.once || e.passive !== s.passive, o = e !== c && (s === c || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Le {
  constructor(e, t, s) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    O(this, e);
  }
}
const q = M.litHtmlPolyfillSupport;
q == null || q(H, D), (M.litHtmlVersions ?? (M.litHtmlVersions = [])).push("3.3.3");
const Fe = (i, e, t) => {
  const s = (t == null ? void 0 : t.renderBefore) ?? e;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = (t == null ? void 0 : t.renderBefore) ?? null;
    s._$litPart$ = r = new D(e.insertBefore(U(), o), o, void 0, t ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const A = globalThis;
class S extends k {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var t;
    const e = super.createRenderRoot();
    return (t = this.renderOptions).renderBefore ?? (t.renderBefore = e.firstChild), e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Fe(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var e;
    super.connectedCallback(), (e = this._$Do) == null || e.setConnected(!0);
  }
  disconnectedCallback() {
    var e;
    super.disconnectedCallback(), (e = this._$Do) == null || e.setConnected(!1);
  }
  render() {
    return C;
  }
}
var ge;
S._$litElement$ = !0, S.finalized = !0, (ge = A.litElementHydrateSupport) == null || ge.call(A, { LitElement: S });
const Z = A.litElementPolyfillSupport;
Z == null || Z({ LitElement: S });
(A.litElementVersions ?? (A.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const we = (i) => (e, t) => {
  t !== void 0 ? t.addInitializer(() => {
    customElements.define(i, e);
  }) : customElements.define(i, e);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Be = { attribute: !0, type: String, converter: F, reflect: !1, hasChanged: X }, Ge = (i = Be, e, t) => {
  const { kind: s, metadata: r } = t;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(t.name, i), s === "accessor") {
    const { name: n } = t;
    return { set(l) {
      const a = e.get.call(this);
      e.set.call(this, l), this.requestUpdate(n, a, i, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(n, void 0, i, l), l;
    } };
  }
  if (s === "setter") {
    const { name: n } = t;
    return function(l) {
      const a = this[n];
      e.call(this, l), this.requestUpdate(n, a, i, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function I(i) {
  return (e, t) => typeof t == "object" ? Ge(i, e, t) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function $(i) {
  return I({ ...i, state: !0, attribute: !1 });
}
function b(i, e) {
  return i.connection.sendMessagePromise(e);
}
const Ve = (i) => b(i, { type: "dash480/panels/list" }), We = (i, e) => b(i, {
  type: "dash480/pages/list",
  panel_entry_id: e
}), qe = (i, e, t, s, r) => b(i, {
  type: "dash480/pages/create",
  panel_entry_id: e,
  title: t,
  columns: s,
  rows: r
}), Ze = (i, e, t) => b(i, { type: "dash480/pages/update", page_id: e, ...t }), Je = (i, e) => b(i, { type: "dash480/pages/delete", page_id: e }), Ke = (i, e) => b(i, {
  type: "dash480/pages/publish",
  panel_entry_id: e
}), Xe = (i, e) => b(i, {
  type: "dash480/preview/render",
  page_draft: e
}), Ye = (i, e) => b(i, {
  type: "dash480/registry/compatible_entities",
  tile_type: e
}), ce = 24, pe = 24, de = 20, ue = 80, Qe = 430, xe = 480;
function et(i, e, t, s) {
  const r = (xe - 2 * ce - (i - 1) * pe) / i, o = (Qe - ue - (e - 1) * de) / e;
  return {
    x: ce + s * (r + pe),
    y: ue + t * (o + de),
    w: r,
    h: o
  };
}
const _e = xe;
var tt = Object.defineProperty, it = Object.getOwnPropertyDescriptor, z = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? it(e, t) : e, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(e, t, r) : n(r)) || r);
  return s && r && tt(e, t, r), r;
};
let E = class extends S {
  constructor() {
    super(...arguments), this.tileType = "entity", this._entities = [], this._search = "";
  }
  connectedCallback() {
    super.connectedCallback(), Ye(this.hass, this.tileType).then((i) => {
      this._entities = i.entities;
    });
  }
  _filtered() {
    const i = this._search.trim().toLowerCase();
    return i ? this._entities.filter(
      (e) => e.friendly_name.toLowerCase().includes(i) || e.entity_id.toLowerCase().includes(i)
    ) : this._entities;
  }
  _pick(i) {
    this.dispatchEvent(new CustomEvent("entity-picked", { detail: { entity_id: i } }));
  }
  _cancel() {
    this.dispatchEvent(new CustomEvent("picker-closed"));
  }
  render() {
    const i = this._filtered();
    return d`
      <div class="backdrop" @click=${this._cancel}>
        <div class="dialog" @click=${(e) => e.stopPropagation()}>
          <input
            class="search"
            placeholder="Search entities…"
            .value=${this._search}
            @input=${(e) => this._search = e.target.value}
          />
          <div class="list">
            ${i.length === 0 ? d`<div class="empty">No matching entities</div>` : i.map(
      (e) => d`
                    <button class="row" @click=${() => this._pick(e.entity_id)}>
                      <span class="name">${e.friendly_name}</span>
                      <span class="id">${e.entity_id}</span>
                    </button>
                  `
    )}
          </div>
          <button class="cancel" @click=${this._cancel}>Cancel</button>
        </div>
      </div>
    `;
  }
};
E.styles = fe`
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .dialog {
      background: var(--card-background-color, #1e1e1e);
      color: var(--primary-text-color, #fff);
      border-radius: 8px;
      padding: 16px;
      width: min(420px, 90vw);
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .search {
      padding: 8px;
      font-size: 14px;
      border-radius: 4px;
      border: 1px solid #666;
      background: transparent;
      color: inherit;
    }
    .list {
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .row {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      padding: 8px;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      border-radius: 4px;
      text-align: left;
    }
    .row:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    .name {
      font-size: 14px;
    }
    .id {
      font-size: 11px;
      opacity: 0.6;
    }
    .empty {
      padding: 16px;
      text-align: center;
      opacity: 0.6;
    }
    .cancel {
      align-self: flex-end;
      padding: 6px 12px;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
    }
  `;
z([
  I({ attribute: !1 })
], E.prototype, "hass", 2);
z([
  I()
], E.prototype, "tileType", 2);
z([
  $()
], E.prototype, "_entities", 2);
z([
  $()
], E.prototype, "_search", 2);
E = z([
  we("dash480-entity-picker")
], E);
var st = Object.defineProperty, rt = Object.getOwnPropertyDescriptor, g = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? rt(e, t) : e, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(e, t, r) : n(r)) || r);
  return s && r && st(e, t, r), r;
};
let _ = class extends S {
  constructor() {
    super(...arguments), this.narrow = !1, this._view = "list", this._panels = [], this._panelId = null, this._pages = [], this._reservedOrders = [], this._editingPage = null, this._previewTiles = [], this._newPageTitle = "", this._typePickerOpenFor = null, this._pickerOpenFor = null, this._status = "";
  }
  connectedCallback() {
    super.connectedCallback(), this._loadPanels();
  }
  async _loadPanels() {
    const { panels: i } = await Ve(this.hass);
    this._panels = i, i.length && !this._panelId && (this._panelId = i[0].entry_id, await this._loadPages());
  }
  async _loadPages() {
    if (!this._panelId) return;
    const { pages: i, reserved_legacy_orders: e } = await We(this.hass, this._panelId);
    this._pages = i, this._reservedOrders = e;
  }
  async _onPanelChange(i) {
    this._panelId = i.target.value, await this._loadPages();
  }
  async _createPage() {
    if (!this._panelId || !this._newPageTitle.trim()) return;
    const { page: i } = await qe(this.hass, this._panelId, this._newPageTitle.trim(), 3, 2);
    this._newPageTitle = "", await this._loadPages(), await this._openEditor(i);
  }
  async _openEditor(i) {
    this._editingPage = i, this._view = "editor", await this._refreshPreview();
  }
  async _refreshPreview() {
    if (!this._editingPage) return;
    const { tiles: i } = await Xe(this.hass, this._editingPage);
    this._previewTiles = i;
  }
  _backToList() {
    this._view = "list", this._editingPage = null, this._loadPages();
  }
  async _deletePage(i) {
    await Je(this.hass, i), await this._loadPages();
  }
  async _save() {
    if (!this._editingPage) return;
    const { title: i, columns: e, rows: t, tiles: s } = this._editingPage;
    await Ze(this.hass, this._editingPage.id, { title: i, columns: e, rows: t, tiles: s }), this._status = "Saved", setTimeout(() => this._status = "", 2e3);
  }
  async _publish() {
    this._panelId && (this._status = "Publishing…", await Ke(this.hass, this._panelId), this._status = "Published", setTimeout(() => this._status = "", 2e3));
  }
  _addTileAt(i, e) {
    this._typePickerOpenFor = { row: i, col: e };
  }
  _chooseTileType(i) {
    this._typePickerOpenFor && (this._pickerOpenFor = { ...this._typePickerOpenFor, type: i }, this._typePickerOpenFor = null);
  }
  async _onEntityPicked(i) {
    if (!this._editingPage || !this._pickerOpenFor) return;
    const { row: e, col: t, type: s } = this._pickerOpenFor, r = {
      id: `t${Date.now()}_${Math.floor(Math.random() * 1e3)}`,
      entity_id: i.detail.entity_id,
      row: e,
      col: t,
      rs: 1,
      cs: 1
    };
    let o;
    if (s === "gauge") {
      const n = Number(window.prompt("Minimum value", "0") ?? "0"), l = Number(window.prompt("Maximum value", "100") ?? "100");
      o = { ...r, type: "gauge", min: Number.isFinite(n) ? n : 0, max: Number.isFinite(l) ? l : 100 };
    } else
      o = { ...r, type: "entity" };
    this._editingPage = {
      ...this._editingPage,
      tiles: [
        ...this._editingPage.tiles.filter((n) => !(n.row === e && n.col === t)),
        o
      ]
    }, this._pickerOpenFor = null, await this._refreshPreview();
  }
  async _removeTile(i) {
    this._editingPage && (this._editingPage = {
      ...this._editingPage,
      tiles: this._editingPage.tiles.filter((e) => e.id !== i)
    }, await this._refreshPreview());
  }
  render() {
    return this.hass ? this._view === "list" ? this._renderList() : this._renderEditor() : c;
  }
  _renderList() {
    return d`
      <div class="wrap">
        <h1>Dash480</h1>
        ${this._panels.length > 1 ? d`
              <select @change=${this._onPanelChange}>
                ${this._panels.map(
      (i) => d`<option value=${i.entry_id} ?selected=${i.entry_id === this._panelId}>
                      ${i.title}
                    </option>`
    )}
              </select>
            ` : c}
        ${this._panels.length === 0 ? d`<p>No Dash480 panels configured yet. Add one from Settings &gt; Devices &amp; Services.</p>` : d`
              <div class="pages">
                ${this._reservedOrders.map(
      (i) => d`<div class="page-card reserved">Page ${i} — legacy (edit via Configure)</div>`
    )}
                ${this._pages.map(
      (i) => d`
                    <div class="page-card">
                      <div class="title" @click=${() => this._openEditor(i)}>
                        Page ${i.page_order}: ${i.title} (${i.tiles.length} tiles)
                      </div>
                      <button @click=${() => this._deletePage(i.id)}>Delete</button>
                    </div>
                  `
    )}
              </div>
              <div class="new-page">
                <input
                  placeholder="New page title"
                  .value=${this._newPageTitle}
                  @input=${(i) => this._newPageTitle = i.target.value}
                />
                <button @click=${this._createPage}>+ New Page</button>
              </div>
            `}
      </div>
    `;
  }
  _renderEditor() {
    const i = this._editingPage, e = [];
    for (let t = 0; t < i.rows; t++)
      for (let s = 0; s < i.columns; s++)
        e.push({ row: t, col: s, rect: et(i.columns, i.rows, t, s) });
    return d`
      <div class="wrap editor">
        <div class="toolbar">
          <button @click=${this._backToList}>&lt; Back</button>
          <span class="page-title">${i.title}</span>
          <button @click=${this._save}>Save</button>
          <button @click=${this._publish}>Publish</button>
          <span class="status">${this._status}</span>
        </div>
        <div class="device" style="width:${_e}px;height:${_e}px;">
          ${e.map(
      (t) => d`
              <div
                class="cell"
                style="left:${t.rect.x}px;top:${t.rect.y}px;width:${t.rect.w}px;height:${t.rect.h}px;"
                @click=${() => this._addTileAt(t.row, t.col)}
              ></div>
            `
    )}
          ${this._previewTiles.map((t) => {
      const s = i.tiles.find((n) => n.id === t.id), r = (s == null ? void 0 : s.type) === "gauge";
      let o = 0;
      if (r && s) {
        const n = s.min ?? 0, l = s.max ?? 100, a = Number(t.state);
        !Number.isNaN(a) && l > n && (o = Math.max(0, Math.min(100, (a - n) / (l - n) * 100)));
      }
      return d`
              <div class="tile" style="left:${t.x}px;top:${t.y}px;width:${t.w}px;height:${t.h}px;">
                <div class="tile-label">${t.friendly_name}</div>
                ${r ? d`
                      <div class="gauge-ring" style="background: conic-gradient(#38bdf8 ${o * 3.6}deg, #334155 0deg);">
                        <div class="gauge-ring-inner">${t.state ?? "--"}</div>
                      </div>
                    ` : d`<div class="tile-state">${t.state ?? "--"}</div>`}
                <button class="tile-remove" @click=${() => s && this._removeTile(s.id)}>×</button>
              </div>
            `;
    })}
        </div>
        <p class="hint">
          Click an empty cell to add a tile. Positions are approximate — verify on the real device.
        </p>
        ${this._typePickerOpenFor ? d`
              <div class="backdrop" @click=${() => this._typePickerOpenFor = null}>
                <div class="type-chooser" @click=${(t) => t.stopPropagation()}>
                  <button @click=${() => this._chooseTileType("entity")}>Entity Tile</button>
                  <button @click=${() => this._chooseTileType("gauge")}>Gauge Tile</button>
                </div>
              </div>
            ` : c}
        ${this._pickerOpenFor ? d`
              <dash480-entity-picker
                .hass=${this.hass}
                .tileType=${this._pickerOpenFor.type}
                @entity-picked=${this._onEntityPicked}
                @picker-closed=${() => this._pickerOpenFor = null}
              ></dash480-entity-picker>
            ` : c}
      </div>
    `;
  }
};
_.styles = fe`
    :host {
      display: block;
      padding: 16px;
      color: var(--primary-text-color, #fff);
      font-family: var(--paper-font-body1_-_font-family, sans-serif);
    }
    .pages {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin: 16px 0;
    }
    .page-card {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      border-radius: 8px;
      background: var(--card-background-color, #1e1e1e);
    }
    .page-card.reserved {
      opacity: 0.5;
    }
    .title {
      cursor: pointer;
    }
    .new-page {
      display: flex;
      gap: 8px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .page-title {
      font-weight: bold;
      flex: 1;
    }
    .status {
      opacity: 0.7;
      font-size: 12px;
    }
    .device {
      position: relative;
      background: #0b1220;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #333;
    }
    .cell {
      position: absolute;
      border: 1px dashed rgba(255, 255, 255, 0.15);
      cursor: pointer;
      border-radius: 8px;
      box-sizing: border-box;
    }
    .cell:hover {
      background: rgba(255, 255, 255, 0.08);
    }
    .tile {
      position: absolute;
      background: #1e293b;
      border-radius: 10px;
      color: #e5e7eb;
      padding: 6px;
      box-sizing: border-box;
      pointer-events: none;
    }
    .tile-label {
      font-size: 11px;
      opacity: 0.7;
    }
    .tile-state {
      font-size: 14px;
      margin-top: 4px;
    }
    .tile-remove {
      position: absolute;
      top: 2px;
      right: 2px;
      pointer-events: auto;
      background: transparent;
      border: none;
      color: #e5e7eb;
      cursor: pointer;
    }
    .gauge-ring {
      width: 60%;
      aspect-ratio: 1;
      margin: 8px auto 0;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .gauge-ring-inner {
      width: 68%;
      aspect-ratio: 1;
      border-radius: 50%;
      background: #1e293b;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      text-align: center;
    }
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .type-chooser {
      background: var(--card-background-color, #1e1e1e);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      gap: 12px;
    }
    .type-chooser button {
      padding: 12px 20px;
      border-radius: 8px;
      border: none;
      background: #334155;
      color: #e5e7eb;
      cursor: pointer;
      font-size: 14px;
    }
    .type-chooser button:hover {
      background: #475569;
    }
    .hint {
      opacity: 0.6;
      font-size: 12px;
    }
  `;
g([
  I({ attribute: !1 })
], _.prototype, "hass", 2);
g([
  I({ type: Boolean })
], _.prototype, "narrow", 2);
g([
  $()
], _.prototype, "_view", 2);
g([
  $()
], _.prototype, "_panels", 2);
g([
  $()
], _.prototype, "_panelId", 2);
g([
  $()
], _.prototype, "_pages", 2);
g([
  $()
], _.prototype, "_reservedOrders", 2);
g([
  $()
], _.prototype, "_editingPage", 2);
g([
  $()
], _.prototype, "_previewTiles", 2);
g([
  $()
], _.prototype, "_newPageTitle", 2);
g([
  $()
], _.prototype, "_typePickerOpenFor", 2);
g([
  $()
], _.prototype, "_pickerOpenFor", 2);
g([
  $()
], _.prototype, "_status", 2);
_ = g([
  we("dash480-panel")
], _);
export {
  _ as Dash480Panel
};
