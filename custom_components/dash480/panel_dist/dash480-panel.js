/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const j = globalThis, J = j.ShadowRoot && (j.ShadyCSS === void 0 || j.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, K = Symbol(), Q = /* @__PURE__ */ new WeakMap();
let $t = class {
  constructor(t, e, i) {
    if (this._$cssResult$ = !0, i !== K) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (J && t === void 0) {
      const i = e !== void 0 && e.length === 1;
      i && (t = Q.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), i && Q.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const Pt = (s) => new $t(typeof s == "string" ? s : s + "", void 0, K), ft = (s, ...t) => {
  const e = s.length === 1 ? s[0] : t.reduce((i, r, n) => i + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + s[n + 1], s[0]);
  return new $t(e, s, K);
}, xt = (s, t) => {
  if (J) s.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const i = document.createElement("style"), r = j.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = e.cssText, s.appendChild(i);
  }
}, tt = J ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const i of t.cssRules) e += i.cssText;
  return Pt(e);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Et, defineProperty: St, getOwnPropertyDescriptor: Ct, getOwnPropertyNames: kt, getOwnPropertySymbols: Ot, getPrototypeOf: Tt } = Object, m = globalThis, et = m.trustedTypes, Ut = et ? et.emptyScript : "", W = m.reactiveElementPolyfillSupport, U = (s, t) => s, B = { toAttribute(s, t) {
  switch (t) {
    case Boolean:
      s = s ? Ut : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, t) {
  let e = s;
  switch (t) {
    case Boolean:
      e = s !== null;
      break;
    case Number:
      e = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(s);
      } catch {
        e = null;
      }
  }
  return e;
} }, X = (s, t) => !Et(s, t), st = { attribute: !0, type: String, converter: B, reflect: !1, useDefault: !1, hasChanged: X };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), m.litPropertyMetadata ?? (m.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let S = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = st) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const i = Symbol(), r = this.getPropertyDescriptor(t, i, e);
      r !== void 0 && St(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, i) {
    const { get: r, set: n } = Ct(this.prototype, t) ?? { get() {
      return this[e];
    }, set(o) {
      this[e] = o;
    } };
    return { get: r, set(o) {
      const l = r == null ? void 0 : r.call(this);
      n == null || n.call(this, o), this.requestUpdate(t, l, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? st;
  }
  static _$Ei() {
    if (this.hasOwnProperty(U("elementProperties"))) return;
    const t = Tt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(U("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(U("properties"))) {
      const e = this.properties, i = [...kt(e), ...Ot(e)];
      for (const r of i) this.createProperty(r, e[r]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [i, r] of e) this.elementProperties.set(i, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, i] of this.elementProperties) {
      const r = this._$Eu(e, i);
      r !== void 0 && this._$Eh.set(r, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const i = new Set(t.flat(1 / 0).reverse());
      for (const r of i) e.unshift(tt(r));
    } else t !== void 0 && e.push(tt(t));
    return e;
  }
  static _$Eu(t, e) {
    const i = e.attribute;
    return i === !1 ? void 0 : typeof i == "string" ? i : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var t;
    this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (t = this.constructor.l) == null || t.forEach((e) => e(this));
  }
  addController(t) {
    var e;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t), this.renderRoot !== void 0 && this.isConnected && ((e = t.hostConnected) == null || e.call(t));
  }
  removeController(t) {
    var e;
    (e = this._$EO) == null || e.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), e = this.constructor.elementProperties;
    for (const i of e.keys()) this.hasOwnProperty(i) && (t.set(i, this[i]), delete this[i]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return xt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    var t;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (t = this._$EO) == null || t.forEach((e) => {
      var i;
      return (i = e.hostConnected) == null ? void 0 : i.call(e);
    });
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    var t;
    (t = this._$EO) == null || t.forEach((e) => {
      var i;
      return (i = e.hostDisconnected) == null ? void 0 : i.call(e);
    });
  }
  attributeChangedCallback(t, e, i) {
    this._$AK(t, i);
  }
  _$ET(t, e) {
    var n;
    const i = this.constructor.elementProperties.get(t), r = this.constructor._$Eu(t, i);
    if (r !== void 0 && i.reflect === !0) {
      const o = (((n = i.converter) == null ? void 0 : n.toAttribute) !== void 0 ? i.converter : B).toAttribute(e, i.type);
      this._$Em = t, o == null ? this.removeAttribute(r) : this.setAttribute(r, o), this._$Em = null;
    }
  }
  _$AK(t, e) {
    var n, o;
    const i = this.constructor, r = i._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const l = i.getPropertyOptions(r), a = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((n = l.converter) == null ? void 0 : n.fromAttribute) !== void 0 ? l.converter : B;
      this._$Em = r;
      const c = a.fromAttribute(e, l.type);
      this[r] = c ?? ((o = this._$Ej) == null ? void 0 : o.get(r)) ?? c, this._$Em = null;
    }
  }
  requestUpdate(t, e, i, r = !1, n) {
    var o;
    if (t !== void 0) {
      const l = this.constructor;
      if (r === !1 && (n = this[t]), i ?? (i = l.getPropertyOptions(t)), !((i.hasChanged ?? X)(n, e) || i.useDefault && i.reflect && n === ((o = this._$Ej) == null ? void 0 : o.get(t)) && !this.hasAttribute(l._$Eu(t, i)))) return;
      this.C(t, e, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: i, reflect: r, wrapped: n }, o) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t) && (this._$Ej.set(t, o ?? e ?? this[t]), n !== !0 || o !== void 0) || (this._$AL.has(t) || (this.hasUpdated || i || (e = void 0), this._$AL.set(t, e)), r === !0 && this._$Em !== t && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (e) {
      Promise.reject(e);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var i;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [n, o] of this._$Ep) this[n] = o;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [n, o] of r) {
        const { wrapped: l } = o, a = this[n];
        l !== !0 || this._$AL.has(n) || a === void 0 || this.C(n, void 0, o, a);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), (i = this._$EO) == null || i.forEach((r) => {
        var n;
        return (n = r.hostUpdate) == null ? void 0 : n.call(r);
      }), this.update(e)) : this._$EM();
    } catch (r) {
      throw t = !1, this._$EM(), r;
    }
    t && this._$AE(e);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    var e;
    (e = this._$EO) == null || e.forEach((i) => {
      var r;
      return (r = i.hostUpdated) == null ? void 0 : r.call(i);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
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
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((e) => this._$ET(e, this[e]))), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[U("elementProperties")] = /* @__PURE__ */ new Map(), S[U("finalized")] = /* @__PURE__ */ new Map(), W == null || W({ ReactiveElement: S }), (m.reactiveElementVersions ?? (m.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const M = globalThis, it = (s) => s, F = M.trustedTypes, rt = F ? F.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, yt = "$lit$", v = `lit$${Math.random().toFixed(9).slice(2)}$`, vt = "?" + v, Mt = `<${vt}>`, x = document, R = () => x.createComment(""), N = (s) => s === null || typeof s != "object" && typeof s != "function", Y = Array.isArray, Rt = (s) => Y(s) || typeof (s == null ? void 0 : s[Symbol.iterator]) == "function", q = `[ 	
\f\r]`, T = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, nt = /-->/g, ot = />/g, A = RegExp(`>|${q}(?:([^\\s"'>=/]+)(${q}*=${q}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), at = /'/g, lt = /"/g, mt = /^(?:script|style|textarea|title)$/i, Nt = (s) => (t, ...e) => ({ _$litType$: s, strings: t, values: e }), _ = Nt(1), k = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), ht = /* @__PURE__ */ new WeakMap(), w = x.createTreeWalker(x, 129);
function bt(s, t) {
  if (!Y(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return rt !== void 0 ? rt.createHTML(t) : t;
}
const Ht = (s, t) => {
  const e = s.length - 1, i = [];
  let r, n = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = T;
  for (let l = 0; l < e; l++) {
    const a = s[l];
    let c, p, h = -1, f = 0;
    for (; f < a.length && (o.lastIndex = f, p = o.exec(a), p !== null); ) f = o.lastIndex, o === T ? p[1] === "!--" ? o = nt : p[1] !== void 0 ? o = ot : p[2] !== void 0 ? (mt.test(p[2]) && (r = RegExp("</" + p[2], "g")), o = A) : p[3] !== void 0 && (o = A) : o === A ? p[0] === ">" ? (o = r ?? T, h = -1) : p[1] === void 0 ? h = -2 : (h = o.lastIndex - p[2].length, c = p[1], o = p[3] === void 0 ? A : p[3] === '"' ? lt : at) : o === lt || o === at ? o = A : o === nt || o === ot ? o = T : (o = A, r = void 0);
    const y = o === A && s[l + 1].startsWith("/>") ? " " : "";
    n += o === T ? a + Mt : h >= 0 ? (i.push(c), a.slice(0, h) + yt + a.slice(h) + v + y) : a + v + (h === -2 ? l : y);
  }
  return [bt(s, n + (s[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), i];
};
class H {
  constructor({ strings: t, _$litType$: e }, i) {
    let r;
    this.parts = [];
    let n = 0, o = 0;
    const l = t.length - 1, a = this.parts, [c, p] = Ht(t, e);
    if (this.el = H.createElement(c, i), w.currentNode = this.el.content, e === 2 || e === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (r = w.nextNode()) !== null && a.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const h of r.getAttributeNames()) if (h.endsWith(yt)) {
          const f = p[o++], y = r.getAttribute(h).split(v), L = /([.?@])?(.*)/.exec(f);
          a.push({ type: 1, index: n, name: L[2], strings: y, ctor: L[1] === "." ? It : L[1] === "?" ? zt : L[1] === "@" ? Lt : V }), r.removeAttribute(h);
        } else h.startsWith(v) && (a.push({ type: 6, index: n }), r.removeAttribute(h));
        if (mt.test(r.tagName)) {
          const h = r.textContent.split(v), f = h.length - 1;
          if (f > 0) {
            r.textContent = F ? F.emptyScript : "";
            for (let y = 0; y < f; y++) r.append(h[y], R()), w.nextNode(), a.push({ type: 2, index: ++n });
            r.append(h[f], R());
          }
        }
      } else if (r.nodeType === 8) if (r.data === vt) a.push({ type: 2, index: n });
      else {
        let h = -1;
        for (; (h = r.data.indexOf(v, h + 1)) !== -1; ) a.push({ type: 7, index: n }), h += v.length - 1;
      }
      n++;
    }
  }
  static createElement(t, e) {
    const i = x.createElement("template");
    return i.innerHTML = t, i;
  }
}
function O(s, t, e = s, i) {
  var o, l;
  if (t === k) return t;
  let r = i !== void 0 ? (o = e._$Co) == null ? void 0 : o[i] : e._$Cl;
  const n = N(t) ? void 0 : t._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== n && ((l = r == null ? void 0 : r._$AO) == null || l.call(r, !1), n === void 0 ? r = void 0 : (r = new n(s), r._$AT(s, e, i)), i !== void 0 ? (e._$Co ?? (e._$Co = []))[i] = r : e._$Cl = r), r !== void 0 && (t = O(s, r._$AS(s, t.values), r, i)), t;
}
class Dt {
  constructor(t, e) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = e;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: e }, parts: i } = this._$AD, r = ((t == null ? void 0 : t.creationScope) ?? x).importNode(e, !0);
    w.currentNode = r;
    let n = w.nextNode(), o = 0, l = 0, a = i[0];
    for (; a !== void 0; ) {
      if (o === a.index) {
        let c;
        a.type === 2 ? c = new D(n, n.nextSibling, this, t) : a.type === 1 ? c = new a.ctor(n, a.name, a.strings, this, t) : a.type === 6 && (c = new jt(n, this, t)), this._$AV.push(c), a = i[++l];
      }
      o !== (a == null ? void 0 : a.index) && (n = w.nextNode(), o++);
    }
    return w.currentNode = x, r;
  }
  p(t) {
    let e = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(t, i, e), e += i.strings.length - 2) : i._$AI(t[e])), e++;
  }
}
class D {
  get _$AU() {
    var t;
    return ((t = this._$AM) == null ? void 0 : t._$AU) ?? this._$Cv;
  }
  constructor(t, e, i, r) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = i, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const e = this._$AM;
    return e !== void 0 && (t == null ? void 0 : t.nodeType) === 11 && (t = e.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, e = this) {
    t = O(this, t, e), N(t) ? t === d || t == null || t === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : t !== this._$AH && t !== k && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Rt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== d && N(this._$AH) ? this._$AA.nextSibling.data = t : this.T(x.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    var n;
    const { values: e, _$litType$: i } = t, r = typeof i == "number" ? this._$AC(t) : (i.el === void 0 && (i.el = H.createElement(bt(i.h, i.h[0]), this.options)), i);
    if (((n = this._$AH) == null ? void 0 : n._$AD) === r) this._$AH.p(e);
    else {
      const o = new Dt(r, this), l = o.u(this.options);
      o.p(e), this.T(l), this._$AH = o;
    }
  }
  _$AC(t) {
    let e = ht.get(t.strings);
    return e === void 0 && ht.set(t.strings, e = new H(t)), e;
  }
  k(t) {
    Y(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let i, r = 0;
    for (const n of t) r === e.length ? e.push(i = new D(this.O(R()), this.O(R()), this, this.options)) : i = e[r], i._$AI(n), r++;
    r < e.length && (this._$AR(i && i._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    var i;
    for ((i = this._$AP) == null ? void 0 : i.call(this, !1, !0, e); t !== this._$AB; ) {
      const r = it(t).nextSibling;
      it(t).remove(), t = r;
    }
  }
  setConnected(t) {
    var e;
    this._$AM === void 0 && (this._$Cv = t, (e = this._$AP) == null || e.call(this, t));
  }
}
class V {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, i, r, n) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = t, this.name = e, this._$AM = r, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = d;
  }
  _$AI(t, e = this, i, r) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) t = O(this, t, e, 0), o = !N(t) || t !== this._$AH && t !== k, o && (this._$AH = t);
    else {
      const l = t;
      let a, c;
      for (t = n[0], a = 0; a < n.length - 1; a++) c = O(this, l[i + a], e, a), c === k && (c = this._$AH[a]), o || (o = !N(c) || c !== this._$AH[a]), c === d ? t = d : t !== d && (t += (c ?? "") + n[a + 1]), this._$AH[a] = c;
    }
    o && !r && this.j(t);
  }
  j(t) {
    t === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class It extends V {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === d ? void 0 : t;
  }
}
class zt extends V {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== d);
  }
}
class Lt extends V {
  constructor(t, e, i, r, n) {
    super(t, e, i, r, n), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = O(this, t, e, 0) ?? d) === k) return;
    const i = this._$AH, r = t === d && i !== d || t.capture !== i.capture || t.once !== i.once || t.passive !== i.passive, n = t !== d && (i === d || r);
    r && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    var e;
    typeof this._$AH == "function" ? this._$AH.call(((e = this.options) == null ? void 0 : e.host) ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class jt {
  constructor(t, e, i) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    O(this, t);
  }
}
const G = M.litHtmlPolyfillSupport;
G == null || G(H, D), (M.litHtmlVersions ?? (M.litHtmlVersions = [])).push("3.3.3");
const Bt = (s, t, e) => {
  const i = (e == null ? void 0 : e.renderBefore) ?? t;
  let r = i._$litPart$;
  if (r === void 0) {
    const n = (e == null ? void 0 : e.renderBefore) ?? null;
    i._$litPart$ = r = new D(t.insertBefore(R(), n), n, void 0, e ?? {});
  }
  return r._$AI(s), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const P = globalThis;
class C extends S {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var e;
    const t = super.createRenderRoot();
    return (e = this.renderOptions).renderBefore ?? (e.renderBefore = t.firstChild), t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Bt(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var t;
    super.connectedCallback(), (t = this._$Do) == null || t.setConnected(!0);
  }
  disconnectedCallback() {
    var t;
    super.disconnectedCallback(), (t = this._$Do) == null || t.setConnected(!1);
  }
  render() {
    return k;
  }
}
var gt;
C._$litElement$ = !0, C.finalized = !0, (gt = P.litElementHydrateSupport) == null || gt.call(P, { LitElement: C });
const Z = P.litElementPolyfillSupport;
Z == null || Z({ LitElement: C });
(P.litElementVersions ?? (P.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const At = (s) => (t, e) => {
  e !== void 0 ? e.addInitializer(() => {
    customElements.define(s, t);
  }) : customElements.define(s, t);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ft = { attribute: !0, type: String, converter: B, reflect: !1, hasChanged: X }, Vt = (s = Ft, t, e) => {
  const { kind: i, metadata: r } = e;
  let n = globalThis.litPropertyMetadata.get(r);
  if (n === void 0 && globalThis.litPropertyMetadata.set(r, n = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), n.set(e.name, s), i === "accessor") {
    const { name: o } = e;
    return { set(l) {
      const a = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(o, a, s, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(o, void 0, s, l), l;
    } };
  }
  if (i === "setter") {
    const { name: o } = e;
    return function(l) {
      const a = this[o];
      t.call(this, l), this.requestUpdate(o, a, s, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function I(s) {
  return (t, e) => typeof e == "object" ? Vt(s, t, e) : ((i, r, n) => {
    const o = r.hasOwnProperty(n);
    return r.constructor.createProperty(n, i), o ? Object.getOwnPropertyDescriptor(r, n) : void 0;
  })(s, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function $(s) {
  return I({ ...s, state: !0, attribute: !1 });
}
function b(s, t) {
  return s.connection.sendMessagePromise(t);
}
const Wt = (s) => b(s, { type: "dash480/panels/list" }), qt = (s, t) => b(s, {
  type: "dash480/pages/list",
  panel_entry_id: t
}), Gt = (s, t, e, i, r) => b(s, {
  type: "dash480/pages/create",
  panel_entry_id: t,
  title: e,
  columns: i,
  rows: r
}), Zt = (s, t, e) => b(s, { type: "dash480/pages/update", page_id: t, ...e }), Jt = (s, t) => b(s, { type: "dash480/pages/delete", page_id: t }), Kt = (s, t) => b(s, {
  type: "dash480/pages/publish",
  panel_entry_id: t
}), Xt = (s, t) => b(s, {
  type: "dash480/preview/render",
  page_draft: t
}), Yt = (s, t) => b(s, {
  type: "dash480/registry/compatible_entities",
  tile_type: t
}), ct = 24, dt = 24, pt = 20, ut = 80, Qt = 430, wt = 480;
function te(s, t, e, i) {
  const r = (wt - 2 * ct - (s - 1) * dt) / s, n = (Qt - ut - (t - 1) * pt) / t;
  return {
    x: ct + i * (r + dt),
    y: ut + e * (n + pt),
    w: r,
    h: n
  };
}
const _t = wt;
var ee = Object.defineProperty, se = Object.getOwnPropertyDescriptor, z = (s, t, e, i) => {
  for (var r = i > 1 ? void 0 : i ? se(t, e) : t, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = (i ? o(t, e, r) : o(r)) || r);
  return i && r && ee(t, e, r), r;
};
let E = class extends C {
  constructor() {
    super(...arguments), this.tileType = "entity", this._entities = [], this._search = "";
  }
  connectedCallback() {
    super.connectedCallback(), Yt(this.hass, this.tileType).then((s) => {
      this._entities = s.entities;
    });
  }
  _filtered() {
    const s = this._search.trim().toLowerCase();
    return s ? this._entities.filter(
      (t) => t.friendly_name.toLowerCase().includes(s) || t.entity_id.toLowerCase().includes(s)
    ) : this._entities;
  }
  _pick(s) {
    this.dispatchEvent(new CustomEvent("entity-picked", { detail: { entity_id: s } }));
  }
  _cancel() {
    this.dispatchEvent(new CustomEvent("picker-closed"));
  }
  render() {
    const s = this._filtered();
    return _`
      <div class="backdrop" @click=${this._cancel}>
        <div class="dialog" @click=${(t) => t.stopPropagation()}>
          <input
            class="search"
            placeholder="Search entities…"
            .value=${this._search}
            @input=${(t) => this._search = t.target.value}
          />
          <div class="list">
            ${s.length === 0 ? _`<div class="empty">No matching entities</div>` : s.map(
      (t) => _`
                    <button class="row" @click=${() => this._pick(t.entity_id)}>
                      <span class="name">${t.friendly_name}</span>
                      <span class="id">${t.entity_id}</span>
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
E.styles = ft`
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
  At("dash480-entity-picker")
], E);
var ie = Object.defineProperty, re = Object.getOwnPropertyDescriptor, g = (s, t, e, i) => {
  for (var r = i > 1 ? void 0 : i ? re(t, e) : t, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = (i ? o(t, e, r) : o(r)) || r);
  return i && r && ie(t, e, r), r;
};
let u = class extends C {
  constructor() {
    super(...arguments), this.narrow = !1, this._view = "list", this._panels = [], this._panelId = null, this._pages = [], this._reservedOrders = [], this._editingPage = null, this._previewTiles = [], this._newPageTitle = "", this._pickerOpenFor = null, this._status = "";
  }
  connectedCallback() {
    super.connectedCallback(), this._loadPanels();
  }
  async _loadPanels() {
    const { panels: s } = await Wt(this.hass);
    this._panels = s, s.length && !this._panelId && (this._panelId = s[0].entry_id, await this._loadPages());
  }
  async _loadPages() {
    if (!this._panelId) return;
    const { pages: s, reserved_legacy_orders: t } = await qt(this.hass, this._panelId);
    this._pages = s, this._reservedOrders = t;
  }
  async _onPanelChange(s) {
    this._panelId = s.target.value, await this._loadPages();
  }
  async _createPage() {
    if (!this._panelId || !this._newPageTitle.trim()) return;
    const { page: s } = await Gt(this.hass, this._panelId, this._newPageTitle.trim(), 3, 2);
    this._newPageTitle = "", await this._loadPages(), await this._openEditor(s);
  }
  async _openEditor(s) {
    this._editingPage = s, this._view = "editor", await this._refreshPreview();
  }
  async _refreshPreview() {
    if (!this._editingPage) return;
    const { tiles: s } = await Xt(this.hass, this._editingPage);
    this._previewTiles = s;
  }
  _backToList() {
    this._view = "list", this._editingPage = null, this._loadPages();
  }
  async _deletePage(s) {
    await Jt(this.hass, s), await this._loadPages();
  }
  async _save() {
    if (!this._editingPage) return;
    const { title: s, columns: t, rows: e, tiles: i } = this._editingPage;
    await Zt(this.hass, this._editingPage.id, { title: s, columns: t, rows: e, tiles: i }), this._status = "Saved", setTimeout(() => this._status = "", 2e3);
  }
  async _publish() {
    this._panelId && (this._status = "Publishing…", await Kt(this.hass, this._panelId), this._status = "Published", setTimeout(() => this._status = "", 2e3));
  }
  _addTileAt(s, t) {
    this._pickerOpenFor = { row: s, col: t };
  }
  async _onEntityPicked(s) {
    if (!this._editingPage || !this._pickerOpenFor) return;
    const { row: t, col: e } = this._pickerOpenFor, i = {
      id: `t${Date.now()}_${Math.floor(Math.random() * 1e3)}`,
      type: "entity",
      entity_id: s.detail.entity_id,
      row: t,
      col: e,
      rs: 1,
      cs: 1
    };
    this._editingPage = {
      ...this._editingPage,
      tiles: [
        ...this._editingPage.tiles.filter((r) => !(r.row === t && r.col === e)),
        i
      ]
    }, this._pickerOpenFor = null, await this._refreshPreview();
  }
  async _removeTile(s) {
    this._editingPage && (this._editingPage = {
      ...this._editingPage,
      tiles: this._editingPage.tiles.filter((t) => t.id !== s)
    }, await this._refreshPreview());
  }
  render() {
    return this.hass ? this._view === "list" ? this._renderList() : this._renderEditor() : d;
  }
  _renderList() {
    return _`
      <div class="wrap">
        <h1>Dash480</h1>
        ${this._panels.length > 1 ? _`
              <select @change=${this._onPanelChange}>
                ${this._panels.map(
      (s) => _`<option value=${s.entry_id} ?selected=${s.entry_id === this._panelId}>
                      ${s.title}
                    </option>`
    )}
              </select>
            ` : d}
        ${this._panels.length === 0 ? _`<p>No Dash480 panels configured yet. Add one from Settings &gt; Devices &amp; Services.</p>` : _`
              <div class="pages">
                ${this._reservedOrders.map(
      (s) => _`<div class="page-card reserved">Page ${s} — legacy (edit via Configure)</div>`
    )}
                ${this._pages.map(
      (s) => _`
                    <div class="page-card">
                      <div class="title" @click=${() => this._openEditor(s)}>
                        Page ${s.page_order}: ${s.title} (${s.tiles.length} tiles)
                      </div>
                      <button @click=${() => this._deletePage(s.id)}>Delete</button>
                    </div>
                  `
    )}
              </div>
              <div class="new-page">
                <input
                  placeholder="New page title"
                  .value=${this._newPageTitle}
                  @input=${(s) => this._newPageTitle = s.target.value}
                />
                <button @click=${this._createPage}>+ New Page</button>
              </div>
            `}
      </div>
    `;
  }
  _renderEditor() {
    const s = this._editingPage, t = [];
    for (let e = 0; e < s.rows; e++)
      for (let i = 0; i < s.columns; i++)
        t.push({ row: e, col: i, rect: te(s.columns, s.rows, e, i) });
    return _`
      <div class="wrap editor">
        <div class="toolbar">
          <button @click=${this._backToList}>&lt; Back</button>
          <span class="page-title">${s.title}</span>
          <button @click=${this._save}>Save</button>
          <button @click=${this._publish}>Publish</button>
          <span class="status">${this._status}</span>
        </div>
        <div class="device" style="width:${_t}px;height:${_t}px;">
          ${t.map(
      (e) => _`
              <div
                class="cell"
                style="left:${e.rect.x}px;top:${e.rect.y}px;width:${e.rect.w}px;height:${e.rect.h}px;"
                @click=${() => this._addTileAt(e.row, e.col)}
              ></div>
            `
    )}
          ${this._previewTiles.map((e) => {
      const i = s.tiles.find((r) => r.id === e.id);
      return _`
              <div class="tile" style="left:${e.x}px;top:${e.y}px;width:${e.w}px;height:${e.h}px;">
                <div class="tile-label">${e.friendly_name}</div>
                <div class="tile-state">${e.state ?? "--"}</div>
                <button class="tile-remove" @click=${() => i && this._removeTile(i.id)}>×</button>
              </div>
            `;
    })}
        </div>
        <p class="hint">
          Click an empty cell to add an entity tile. Positions are approximate — verify on the real device.
        </p>
        ${this._pickerOpenFor ? _`
              <dash480-entity-picker
                .hass=${this.hass}
                tileType="entity"
                @entity-picked=${this._onEntityPicked}
                @picker-closed=${() => this._pickerOpenFor = null}
              ></dash480-entity-picker>
            ` : d}
      </div>
    `;
  }
};
u.styles = ft`
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
    .hint {
      opacity: 0.6;
      font-size: 12px;
    }
  `;
g([
  I({ attribute: !1 })
], u.prototype, "hass", 2);
g([
  I({ type: Boolean })
], u.prototype, "narrow", 2);
g([
  $()
], u.prototype, "_view", 2);
g([
  $()
], u.prototype, "_panels", 2);
g([
  $()
], u.prototype, "_panelId", 2);
g([
  $()
], u.prototype, "_pages", 2);
g([
  $()
], u.prototype, "_reservedOrders", 2);
g([
  $()
], u.prototype, "_editingPage", 2);
g([
  $()
], u.prototype, "_previewTiles", 2);
g([
  $()
], u.prototype, "_newPageTitle", 2);
g([
  $()
], u.prototype, "_pickerOpenFor", 2);
g([
  $()
], u.prototype, "_status", 2);
u = g([
  At("dash480-panel")
], u);
export {
  u as Dash480Panel
};
