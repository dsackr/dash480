/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const F = globalThis, X = F.ShadowRoot && (F.ShadyCSS === void 0 || F.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Y = Symbol(), se = /* @__PURE__ */ new WeakMap();
let be = class {
  constructor(e, t, s) {
    if (this._$cssResult$ = !0, s !== Y) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (X && e === void 0) {
      const s = t !== void 0 && t.length === 1;
      s && (e = se.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), s && se.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const Ee = (i) => new be(typeof i == "string" ? i : i + "", void 0, Y), Q = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((s, r, n) => s + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[n + 1], i[0]);
  return new be(t, i, Y);
}, Se = (i, e) => {
  if (X) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const s = document.createElement("style"), r = F.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = t.cssText, i.appendChild(s);
  }
}, re = X ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const s of e.cssRules) t += s.cssText;
  return Ee(t);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: Ce, defineProperty: Oe, getOwnPropertyDescriptor: Te, getOwnPropertyNames: Me, getOwnPropertySymbols: Ne, getPrototypeOf: Ue } = Object, b = globalThis, ne = b.trustedTypes, Re = ne ? ne.emptyScript : "", V = b.reactiveElementPolyfillSupport, U = (i, e) => i, B = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? Re : null;
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
} }, ee = (i, e) => !Ce(i, e), ae = { attribute: !0, type: String, converter: B, reflect: !1, useDefault: !1, hasChanged: ee };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), b.litPropertyMetadata ?? (b.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let S = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = ae) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(e, s, t);
      r !== void 0 && Oe(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, s) {
    const { get: r, set: n } = Te(this.prototype, e) ?? { get() {
      return this[t];
    }, set(a) {
      this[t] = a;
    } };
    return { get: r, set(a) {
      const l = r == null ? void 0 : r.call(this);
      n == null || n.call(this, a), this.requestUpdate(e, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ae;
  }
  static _$Ei() {
    if (this.hasOwnProperty(U("elementProperties"))) return;
    const e = Ue(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(U("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(U("properties"))) {
      const t = this.properties, s = [...Me(t), ...Ne(t)];
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
      for (const r of s) t.unshift(re(r));
    } else e !== void 0 && t.push(re(e));
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
    return Se(e, this.constructor.elementStyles), e;
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
    var n;
    const s = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, s);
    if (r !== void 0 && s.reflect === !0) {
      const a = (((n = s.converter) == null ? void 0 : n.toAttribute) !== void 0 ? s.converter : B).toAttribute(t, s.type);
      this._$Em = e, a == null ? this.removeAttribute(r) : this.setAttribute(r, a), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var n, a;
    const s = this.constructor, r = s._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const l = s.getPropertyOptions(r), o = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((n = l.converter) == null ? void 0 : n.fromAttribute) !== void 0 ? l.converter : B;
      this._$Em = r;
      const h = o.fromAttribute(t, l.type);
      this[r] = h ?? ((a = this._$Ej) == null ? void 0 : a.get(r)) ?? h, this._$Em = null;
    }
  }
  requestUpdate(e, t, s, r = !1, n) {
    var a;
    if (e !== void 0) {
      const l = this.constructor;
      if (r === !1 && (n = this[e]), s ?? (s = l.getPropertyOptions(e)), !((s.hasChanged ?? ee)(n, t) || s.useDefault && s.reflect && n === ((a = this._$Ej) == null ? void 0 : a.get(e)) && !this.hasAttribute(l._$Eu(e, s)))) return;
      this.C(e, t, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: s, reflect: r, wrapped: n }, a) {
    s && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), n !== !0 || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || s || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
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
        for (const [n, a] of this._$Ep) this[n] = a;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [n, a] of r) {
        const { wrapped: l } = a, o = this[n];
        l !== !0 || this._$AL.has(n) || o === void 0 || this.C(n, void 0, a, o);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (s = this._$EO) == null || s.forEach((r) => {
        var n;
        return (n = r.hostUpdate) == null ? void 0 : n.call(r);
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
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[U("elementProperties")] = /* @__PURE__ */ new Map(), S[U("finalized")] = /* @__PURE__ */ new Map(), V == null || V({ ReactiveElement: S }), (b.reactiveElementVersions ?? (b.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const R = globalThis, oe = (i) => i, W = R.trustedTypes, le = W ? W.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, xe = "$lit$", m = `lit$${Math.random().toFixed(9).slice(2)}$`, we = "?" + m, De = `<${we}>`, k = document, D = () => k.createComment(""), I = (i) => i === null || typeof i != "object" && typeof i != "function", te = Array.isArray, Ie = (i) => te(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", Z = `[ 	
\f\r]`, N = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ce = /-->/g, he = />/g, x = RegExp(`>|${Z}(?:([^\\s"'>=/]+)(${Z}*=${Z}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), pe = /'/g, de = /"/g, Pe = /^(?:script|style|textarea|title)$/i, He = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), p = He(1), C = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), ue = /* @__PURE__ */ new WeakMap(), w = k.createTreeWalker(k, 129);
function Ae(i, e) {
  if (!te(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return le !== void 0 ? le.createHTML(e) : e;
}
const ze = (i, e) => {
  const t = i.length - 1, s = [];
  let r, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", a = N;
  for (let l = 0; l < t; l++) {
    const o = i[l];
    let h, u, c = -1, $ = 0;
    for (; $ < o.length && (a.lastIndex = $, u = a.exec(o), u !== null); ) $ = a.lastIndex, a === N ? u[1] === "!--" ? a = ce : u[1] !== void 0 ? a = he : u[2] !== void 0 ? (Pe.test(u[2]) && (r = RegExp("</" + u[2], "g")), a = x) : u[3] !== void 0 && (a = x) : a === x ? u[0] === ">" ? (a = r ?? N, c = -1) : u[1] === void 0 ? c = -2 : (c = a.lastIndex - u[2].length, h = u[1], a = u[3] === void 0 ? x : u[3] === '"' ? de : pe) : a === de || a === pe ? a = x : a === ce || a === he ? a = N : (a = x, r = void 0);
    const y = a === x && i[l + 1].startsWith("/>") ? " " : "";
    n += a === N ? o + De : c >= 0 ? (s.push(h), o.slice(0, c) + xe + o.slice(c) + m + y) : o + m + (c === -2 ? l : y);
  }
  return [Ae(i, n + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), s];
};
class H {
  constructor({ strings: e, _$litType$: t }, s) {
    let r;
    this.parts = [];
    let n = 0, a = 0;
    const l = e.length - 1, o = this.parts, [h, u] = ze(e, t);
    if (this.el = H.createElement(h, s), w.currentNode = this.el.content, t === 2 || t === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (r = w.nextNode()) !== null && o.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const c of r.getAttributeNames()) if (c.endsWith(xe)) {
          const $ = u[a++], y = r.getAttribute(c).split(m), L = /([.?@])?(.*)/.exec($);
          o.push({ type: 1, index: n, name: L[2], strings: y, ctor: L[1] === "." ? Le : L[1] === "?" ? Fe : L[1] === "@" ? Be : G }), r.removeAttribute(c);
        } else c.startsWith(m) && (o.push({ type: 6, index: n }), r.removeAttribute(c));
        if (Pe.test(r.tagName)) {
          const c = r.textContent.split(m), $ = c.length - 1;
          if ($ > 0) {
            r.textContent = W ? W.emptyScript : "";
            for (let y = 0; y < $; y++) r.append(c[y], D()), w.nextNode(), o.push({ type: 2, index: ++n });
            r.append(c[$], D());
          }
        }
      } else if (r.nodeType === 8) if (r.data === we) o.push({ type: 2, index: n });
      else {
        let c = -1;
        for (; (c = r.data.indexOf(m, c + 1)) !== -1; ) o.push({ type: 7, index: n }), c += m.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const s = k.createElement("template");
    return s.innerHTML = e, s;
  }
}
function O(i, e, t = i, s) {
  var a, l;
  if (e === C) return e;
  let r = s !== void 0 ? (a = t._$Co) == null ? void 0 : a[s] : t._$Cl;
  const n = I(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== n && ((l = r == null ? void 0 : r._$AO) == null || l.call(r, !1), n === void 0 ? r = void 0 : (r = new n(i), r._$AT(i, t, s)), s !== void 0 ? (t._$Co ?? (t._$Co = []))[s] = r : t._$Cl = r), r !== void 0 && (e = O(i, r._$AS(i, e.values), r, s)), e;
}
class je {
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
    const { el: { content: t }, parts: s } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? k).importNode(t, !0);
    w.currentNode = r;
    let n = w.nextNode(), a = 0, l = 0, o = s[0];
    for (; o !== void 0; ) {
      if (a === o.index) {
        let h;
        o.type === 2 ? h = new z(n, n.nextSibling, this, e) : o.type === 1 ? h = new o.ctor(n, o.name, o.strings, this, e) : o.type === 6 && (h = new We(n, this, e)), this._$AV.push(h), o = s[++l];
      }
      a !== (o == null ? void 0 : o.index) && (n = w.nextNode(), a++);
    }
    return w.currentNode = k, r;
  }
  p(e) {
    let t = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(e, s, t), t += s.strings.length - 2) : s._$AI(e[t])), t++;
  }
}
class z {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, s, r) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = s, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
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
    e = O(this, e, t), I(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== C && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Ie(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && I(this._$AH) ? this._$AA.nextSibling.data = e : this.T(k.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var n;
    const { values: t, _$litType$: s } = e, r = typeof s == "number" ? this._$AC(e) : (s.el === void 0 && (s.el = H.createElement(Ae(s.h, s.h[0]), this.options)), s);
    if (((n = this._$AH) == null ? void 0 : n._$AD) === r) this._$AH.p(t);
    else {
      const a = new je(r, this), l = a.u(this.options);
      a.p(t), this.T(l), this._$AH = a;
    }
  }
  _$AC(e) {
    let t = ue.get(e.strings);
    return t === void 0 && ue.set(e.strings, t = new H(e)), t;
  }
  k(e) {
    te(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let s, r = 0;
    for (const n of e) r === t.length ? t.push(s = new z(this.O(D()), this.O(D()), this, this.options)) : s = t[r], s._$AI(n), r++;
    r < t.length && (this._$AR(s && s._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var s;
    for ((s = this._$AP) == null ? void 0 : s.call(this, !1, !0, t); e !== this._$AB; ) {
      const r = oe(e).nextSibling;
      oe(e).remove(), e = r;
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
  constructor(e, t, s, r, n) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = n, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = d;
  }
  _$AI(e, t = this, s, r) {
    const n = this.strings;
    let a = !1;
    if (n === void 0) e = O(this, e, t, 0), a = !I(e) || e !== this._$AH && e !== C, a && (this._$AH = e);
    else {
      const l = e;
      let o, h;
      for (e = n[0], o = 0; o < n.length - 1; o++) h = O(this, l[s + o], t, o), h === C && (h = this._$AH[o]), a || (a = !I(h) || h !== this._$AH[o]), h === d ? e = d : e !== d && (e += (h ?? "") + n[o + 1]), this._$AH[o] = h;
    }
    a && !r && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Le extends G {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class Fe extends G {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class Be extends G {
  constructor(e, t, s, r, n) {
    super(e, t, s, r, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = O(this, e, t, 0) ?? d) === C) return;
    const s = this._$AH, r = e === d && s !== d || e.capture !== s.capture || e.once !== s.once || e.passive !== s.passive, n = e !== d && (s === d || r);
    r && this.element.removeEventListener(this.name, this, s), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class We {
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
const J = R.litHtmlPolyfillSupport;
J == null || J(H, z), (R.litHtmlVersions ?? (R.litHtmlVersions = [])).push("3.3.3");
const Ge = (i, e, t) => {
  const s = (t == null ? void 0 : t.renderBefore) ?? e;
  let r = s._$litPart$;
  if (r === void 0) {
    const n = (t == null ? void 0 : t.renderBefore) ?? null;
    s._$litPart$ = r = new z(e.insertBefore(D(), n), n, void 0, t ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const P = globalThis;
class A extends S {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ge(t, this.renderRoot, this.renderOptions);
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
var me;
A._$litElement$ = !0, A.finalized = !0, (me = P.litElementHydrateSupport) == null || me.call(P, { LitElement: A });
const K = P.litElementPolyfillSupport;
K == null || K({ LitElement: A });
(P.litElementVersions ?? (P.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ie = (i) => (e, t) => {
  t !== void 0 ? t.addInitializer(() => {
    customElements.define(i, e);
  }) : customElements.define(i, e);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const qe = { attribute: !0, type: String, converter: B, reflect: !1, hasChanged: ee }, Ve = (i = qe, e, t) => {
  const { kind: s, metadata: r } = t;
  let n = globalThis.litPropertyMetadata.get(r);
  if (n === void 0 && globalThis.litPropertyMetadata.set(r, n = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), n.set(t.name, i), s === "accessor") {
    const { name: a } = t;
    return { set(l) {
      const o = e.get.call(this);
      e.set.call(this, l), this.requestUpdate(a, o, i, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(a, void 0, i, l), l;
    } };
  }
  if (s === "setter") {
    const { name: a } = t;
    return function(l) {
      const o = this[a];
      e.call(this, l), this.requestUpdate(a, o, i, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function M(i) {
  return (e, t) => typeof t == "object" ? Ve(i, e, t) : ((s, r, n) => {
    const a = r.hasOwnProperty(n);
    return r.constructor.createProperty(n, s), a ? Object.getOwnPropertyDescriptor(r, n) : void 0;
  })(i, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function g(i) {
  return M({ ...i, state: !0, attribute: !1 });
}
function v(i, e) {
  return i.connection.sendMessagePromise(e);
}
const Ze = (i) => v(i, { type: "dash480/panels/list" }), _e = (i, e) => v(i, {
  type: "dash480/pages/list",
  panel_entry_id: e
}), Je = (i, e, t, s, r) => v(i, {
  type: "dash480/pages/create",
  panel_entry_id: e,
  title: t,
  columns: s,
  rows: r
}), Ke = (i, e, t) => v(i, { type: "dash480/pages/update", page_id: e, ...t }), Xe = (i, e) => v(i, { type: "dash480/pages/delete", page_id: e }), Ye = (i, e) => v(i, {
  type: "dash480/pages/publish",
  panel_entry_id: e
}), Qe = (i, e) => v(i, {
  type: "dash480/preview/render",
  page_draft: e
}), et = (i, e) => v(i, {
  type: "dash480/registry/compatible_entities",
  tile_type: e
}), tt = (i) => v(i, { type: "dash480/registry/areas" }), it = (i, e, t, s, r) => v(i, {
  type: "dash480/pages/generate_from_area",
  panel_entry_id: e,
  area_id: t,
  mode: s,
  ...r ? { target_page_id: r } : {}
}), ge = 24, fe = 24, $e = 20, ye = 80, st = 430, ke = 480;
function rt(i, e, t, s) {
  const r = (ke - 2 * ge - (i - 1) * fe) / i, n = (st - ye - (e - 1) * $e) / e;
  return {
    x: ge + s * (r + fe),
    y: ye + t * (n + $e),
    w: r,
    h: n
  };
}
const ve = ke;
var nt = Object.defineProperty, at = Object.getOwnPropertyDescriptor, j = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? at(e, t) : e, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (r = (s ? a(e, t, r) : a(r)) || r);
  return s && r && nt(e, t, r), r;
};
let E = class extends A {
  constructor() {
    super(...arguments), this.tileType = "entity", this._entities = [], this._search = "";
  }
  connectedCallback() {
    super.connectedCallback(), et(this.hass, this.tileType).then((i) => {
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
    return p`
      <div class="backdrop" @click=${this._cancel}>
        <div class="dialog" @click=${(e) => e.stopPropagation()}>
          <input
            class="search"
            placeholder="Search entities…"
            .value=${this._search}
            @input=${(e) => this._search = e.target.value}
          />
          <div class="list">
            ${i.length === 0 ? p`<div class="empty">No matching entities</div>` : i.map(
      (e) => p`
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
E.styles = Q`
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
j([
  M({ attribute: !1 })
], E.prototype, "hass", 2);
j([
  M()
], E.prototype, "tileType", 2);
j([
  g()
], E.prototype, "_entities", 2);
j([
  g()
], E.prototype, "_search", 2);
E = j([
  ie("dash480-entity-picker")
], E);
var ot = Object.defineProperty, lt = Object.getOwnPropertyDescriptor, q = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? lt(e, t) : e, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (r = (s ? a(e, t, r) : a(r)) || r);
  return s && r && ot(e, t, r), r;
};
let T = class extends A {
  constructor() {
    super(...arguments), this._areas = [], this._search = "";
  }
  connectedCallback() {
    super.connectedCallback(), tt(this.hass).then((i) => {
      this._areas = i.areas;
    });
  }
  _filtered() {
    const i = this._search.trim().toLowerCase();
    return i ? this._areas.filter((e) => e.name.toLowerCase().includes(i)) : this._areas;
  }
  _pick(i) {
    this.dispatchEvent(new CustomEvent("area-picked", { detail: { area_id: i } }));
  }
  _cancel() {
    this.dispatchEvent(new CustomEvent("picker-closed"));
  }
  render() {
    const i = this._filtered();
    return p`
      <div class="backdrop" @click=${this._cancel}>
        <div class="dialog" @click=${(e) => e.stopPropagation()}>
          <input
            class="search"
            placeholder="Search areas…"
            .value=${this._search}
            @input=${(e) => this._search = e.target.value}
          />
          <div class="list">
            ${i.length === 0 ? p`<div class="empty">No matching areas</div>` : i.map(
      (e) => p`
                    <button class="row" @click=${() => this._pick(e.area_id)}>
                      <span class="name">${e.name}</span>
                      <span class="counts">${e.entity_count} entities · ${e.device_count} devices</span>
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
T.styles = Q`
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
    .counts {
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
q([
  M({ attribute: !1 })
], T.prototype, "hass", 2);
q([
  g()
], T.prototype, "_areas", 2);
q([
  g()
], T.prototype, "_search", 2);
T = q([
  ie("dash480-area-picker")
], T);
var ct = Object.defineProperty, ht = Object.getOwnPropertyDescriptor, f = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? ht(e, t) : e, n = i.length - 1, a; n >= 0; n--)
    (a = i[n]) && (r = (s ? a(e, t, r) : a(r)) || r);
  return s && r && ct(e, t, r), r;
};
let _ = class extends A {
  constructor() {
    super(...arguments), this.narrow = !1, this._view = "list", this._panels = [], this._panelId = null, this._pages = [], this._reservedOrders = [], this._editingPage = null, this._previewTiles = [], this._newPageTitle = "", this._typePickerOpenFor = null, this._pickerOpenFor = null, this._areaPickerMode = null, this._status = "";
  }
  connectedCallback() {
    super.connectedCallback(), this._loadPanels();
  }
  async _loadPanels() {
    const { panels: i } = await Ze(this.hass);
    this._panels = i, i.length && !this._panelId && (this._panelId = i[0].entry_id, await this._loadPages());
  }
  async _loadPages() {
    if (!this._panelId) return;
    const { pages: i, reserved_legacy_orders: e } = await _e(this.hass, this._panelId);
    this._pages = i, this._reservedOrders = e;
  }
  async _onPanelChange(i) {
    this._panelId = i.target.value, await this._loadPages();
  }
  async _createPage() {
    if (!this._panelId || !this._newPageTitle.trim()) return;
    const { page: i } = await Je(this.hass, this._panelId, this._newPageTitle.trim(), 3, 2);
    this._newPageTitle = "", await this._loadPages(), await this._openEditor(i);
  }
  async _openEditor(i) {
    this._editingPage = i, this._view = "editor", await this._refreshPreview();
  }
  async _refreshPreview() {
    if (!this._editingPage) return;
    const { tiles: i } = await Qe(this.hass, this._editingPage);
    this._previewTiles = i;
  }
  _backToList() {
    this._view = "list", this._editingPage = null, this._loadPages();
  }
  async _deletePage(i) {
    await Xe(this.hass, i), await this._loadPages();
  }
  async _save() {
    if (!this._editingPage) return;
    const { title: i, columns: e, rows: t, tiles: s } = this._editingPage;
    await Ke(this.hass, this._editingPage.id, { title: i, columns: e, rows: t, tiles: s }), this._status = "Saved", setTimeout(() => this._status = "", 2e3);
  }
  async _publish() {
    this._panelId && (this._status = "Publishing…", await Ye(this.hass, this._panelId), this._status = "Published", setTimeout(() => this._status = "", 2e3));
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
    let n;
    if (s === "gauge") {
      const a = Number(window.prompt("Minimum value", "0") ?? "0"), l = Number(window.prompt("Maximum value", "100") ?? "100");
      n = { ...r, type: "gauge", min: Number.isFinite(a) ? a : 0, max: Number.isFinite(l) ? l : 100 };
    } else s === "weather" ? n = { ...r, type: "weather" } : n = { ...r, type: "entity" };
    this._editingPage = {
      ...this._editingPage,
      tiles: [
        ...this._editingPage.tiles.filter((a) => !(a.row === e && a.col === t)),
        n
      ]
    }, this._pickerOpenFor = null, await this._refreshPreview();
  }
  async _removeTile(i) {
    this._editingPage && (this._editingPage = {
      ...this._editingPage,
      tiles: this._editingPage.tiles.filter((e) => e.id !== i)
    }, await this._refreshPreview());
  }
  _openAreaPicker(i) {
    this._areaPickerMode = i;
  }
  async _onAreaPicked(i) {
    var n;
    const e = this._areaPickerMode;
    if (this._areaPickerMode = null, !e || !this._panelId) return;
    const t = e === "append" ? (n = this._editingPage) == null ? void 0 : n.id : void 0;
    if (e === "append" && !t) return;
    e === "append" && await this._save();
    const s = await it(this.hass, this._panelId, i.detail.area_id, e, t), r = s.skipped_entity_ids.length + s.skipped_incompatible_count;
    if (this._status = `Placed ${s.placed_count} entities${r ? `, ${r} skipped` : ""}`, setTimeout(() => this._status = "", 4e3), e === "append" && this._editingPage) {
      const { pages: a } = await _e(this.hass, this._panelId), l = a.find((o) => o.id === this._editingPage.id);
      l && (this._editingPage = l, await this._refreshPreview());
    } else
      await this._loadPages();
  }
  render() {
    return this.hass ? p`
      ${this._view === "list" ? this._renderList() : this._renderEditor()}
      ${this._areaPickerMode ? p`
            <dash480-area-picker
              .hass=${this.hass}
              @area-picked=${this._onAreaPicked}
              @picker-closed=${() => this._areaPickerMode = null}
            ></dash480-area-picker>
          ` : d}
    ` : d;
  }
  _renderList() {
    return p`
      <div class="wrap">
        <h1>Dash480</h1>
        ${this._panels.length > 1 ? p`
              <select @change=${this._onPanelChange}>
                ${this._panels.map(
      (i) => p`<option value=${i.entry_id} ?selected=${i.entry_id === this._panelId}>
                      ${i.title}
                    </option>`
    )}
              </select>
            ` : d}
        ${this._panels.length === 0 ? p`<p>No Dash480 panels configured yet. Add one from Settings &gt; Devices &amp; Services.</p>` : p`
              <div class="pages">
                ${this._reservedOrders.map(
      (i) => p`<div class="page-card reserved">Page ${i} — legacy (edit via Configure)</div>`
    )}
                ${this._pages.map(
      (i) => p`
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
                <button @click=${() => this._openAreaPicker("new_page")}>+ Generate Page from Area</button>
              </div>
              <span class="status">${this._status}</span>
            `}
      </div>
    `;
  }
  _renderEditor() {
    const i = this._editingPage, e = [];
    for (let t = 0; t < i.rows; t++)
      for (let s = 0; s < i.columns; s++)
        e.push({ row: t, col: s, rect: rt(i.columns, i.rows, t, s) });
    return p`
      <div class="wrap editor">
        <div class="toolbar">
          <button @click=${this._backToList}>&lt; Back</button>
          <span class="page-title">${i.title}</span>
          <button @click=${() => this._openAreaPicker("append")}>+ Add Area Entities</button>
          <button @click=${this._save}>Save</button>
          <button @click=${this._publish}>Publish</button>
          <span class="status">${this._status}</span>
        </div>
        <div class="device" style="width:${ve}px;height:${ve}px;">
          ${e.map(
      (t) => p`
              <div
                class="cell"
                style="left:${t.rect.x}px;top:${t.rect.y}px;width:${t.rect.w}px;height:${t.rect.h}px;"
                @click=${() => this._addTileAt(t.row, t.col)}
              ></div>
            `
    )}
          ${this._previewTiles.map((t) => {
      var h, u;
      const s = i.tiles.find((c) => c.id === t.id), r = (s == null ? void 0 : s.type) === "gauge", n = (s == null ? void 0 : s.type) === "weather";
      let a = 0;
      if (r && s) {
        const c = s.min ?? 0, $ = s.max ?? 100, y = Number(t.state);
        !Number.isNaN(y) && $ > c && (a = Math.max(0, Math.min(100, (y - c) / ($ - c) * 100)));
      }
      const l = (h = t.attributes) == null ? void 0 : h.temperature, o = ((u = t.attributes) == null ? void 0 : u.temperature_unit) ?? "";
      return p`
              <div class="tile" style="left:${t.x}px;top:${t.y}px;width:${t.w}px;height:${t.h}px;">
                <div class="tile-label">${t.friendly_name}</div>
                ${r ? p`
                      <div class="gauge-ring" style="background: conic-gradient(#38bdf8 ${a * 3.6}deg, #334155 0deg);">
                        <div class="gauge-ring-inner">${t.state ?? "--"}</div>
                      </div>
                    ` : n ? p`
                        <div class="weather-condition">${t.state ?? "--"}</div>
                        <div class="tile-state">${l !== void 0 ? `${l}${o}` : "--"}</div>
                      ` : p`<div class="tile-state">${t.state ?? "--"}</div>`}
                <button class="tile-remove" @click=${() => s && this._removeTile(s.id)}>×</button>
              </div>
            `;
    })}
        </div>
        <p class="hint">
          Click an empty cell to add a tile. Positions are approximate — verify on the real device.
        </p>
        ${this._typePickerOpenFor ? p`
              <div class="backdrop" @click=${() => this._typePickerOpenFor = null}>
                <div class="type-chooser" @click=${(t) => t.stopPropagation()}>
                  <button @click=${() => this._chooseTileType("entity")}>Entity Tile</button>
                  <button @click=${() => this._chooseTileType("gauge")}>Gauge Tile</button>
                  <button @click=${() => this._chooseTileType("weather")}>Weather Tile</button>
                </div>
              </div>
            ` : d}
        ${this._pickerOpenFor ? p`
              <dash480-entity-picker
                .hass=${this.hass}
                .tileType=${this._pickerOpenFor.type}
                @entity-picked=${this._onEntityPicked}
                @picker-closed=${() => this._pickerOpenFor = null}
              ></dash480-entity-picker>
            ` : d}
      </div>
    `;
  }
};
_.styles = Q`
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
    .weather-condition {
      font-size: 20px;
      margin-top: 12px;
      text-align: center;
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
f([
  M({ attribute: !1 })
], _.prototype, "hass", 2);
f([
  M({ type: Boolean })
], _.prototype, "narrow", 2);
f([
  g()
], _.prototype, "_view", 2);
f([
  g()
], _.prototype, "_panels", 2);
f([
  g()
], _.prototype, "_panelId", 2);
f([
  g()
], _.prototype, "_pages", 2);
f([
  g()
], _.prototype, "_reservedOrders", 2);
f([
  g()
], _.prototype, "_editingPage", 2);
f([
  g()
], _.prototype, "_previewTiles", 2);
f([
  g()
], _.prototype, "_newPageTitle", 2);
f([
  g()
], _.prototype, "_typePickerOpenFor", 2);
f([
  g()
], _.prototype, "_pickerOpenFor", 2);
f([
  g()
], _.prototype, "_areaPickerMode", 2);
f([
  g()
], _.prototype, "_status", 2);
_ = f([
  ie("dash480-panel")
], _);
export {
  _ as Dash480Panel
};
