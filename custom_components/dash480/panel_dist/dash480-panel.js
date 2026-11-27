/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const ie = globalThis, Ae = ie.ShadowRoot && (ie.ShadyCSS === void 0 || ie.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Ee = Symbol(), Ue = /* @__PURE__ */ new WeakMap();
let Qe = class {
  constructor(e, s, i) {
    if (this._$cssResult$ = !0, i !== Ee) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = s;
  }
  get styleSheet() {
    let e = this.o;
    const s = this.t;
    if (Ae && e === void 0) {
      const i = s !== void 0 && s.length === 1;
      i && (e = Ue.get(s)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && Ue.set(s, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const pt = (t) => new Qe(typeof t == "string" ? t : t + "", void 0, Ee), q = (t, ...e) => {
  const s = t.length === 1 ? t[0] : e.reduce((i, r, n) => i + ((a) => {
    if (a._$cssResult$ === !0) return a.cssText;
    if (typeof a == "number") return a;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + a + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + t[n + 1], t[0]);
  return new Qe(s, t, Ee);
}, ut = (t, e) => {
  if (Ae) t.adoptedStyleSheets = e.map((s) => s instanceof CSSStyleSheet ? s : s.styleSheet);
  else for (const s of e) {
    const i = document.createElement("style"), r = ie.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = s.cssText, t.appendChild(i);
  }
}, He = Ae ? (t) => t : (t) => t instanceof CSSStyleSheet ? ((e) => {
  let s = "";
  for (const i of e.cssRules) s += i.cssText;
  return pt(s);
})(t) : t;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: _t, defineProperty: gt, getOwnPropertyDescriptor: ft, getOwnPropertyNames: vt, getOwnPropertySymbols: $t, getPrototypeOf: bt } = Object, S = globalThis, Le = S.trustedTypes, yt = Le ? Le.emptyScript : "", pe = S.reactiveElementPolyfillSupport, X = (t, e) => t, re = { toAttribute(t, e) {
  switch (e) {
    case Boolean:
      t = t ? yt : null;
      break;
    case Object:
    case Array:
      t = t == null ? t : JSON.stringify(t);
  }
  return t;
}, fromAttribute(t, e) {
  let s = t;
  switch (e) {
    case Boolean:
      s = t !== null;
      break;
    case Number:
      s = t === null ? null : Number(t);
      break;
    case Object:
    case Array:
      try {
        s = JSON.parse(t);
      } catch {
        s = null;
      }
  }
  return s;
} }, Pe = (t, e) => !_t(t, e), je = { attribute: !0, type: String, converter: re, reflect: !1, useDefault: !1, hasChanged: Pe };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), S.litPropertyMetadata ?? (S.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let U = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, s = je) {
    if (s.state && (s.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((s = Object.create(s)).wrapped = !0), this.elementProperties.set(e, s), !s.noAccessor) {
      const i = Symbol(), r = this.getPropertyDescriptor(e, i, s);
      r !== void 0 && gt(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, s, i) {
    const { get: r, set: n } = ft(this.prototype, e) ?? { get() {
      return this[s];
    }, set(a) {
      this[s] = a;
    } };
    return { get: r, set(a) {
      const o = r == null ? void 0 : r.call(this);
      n == null || n.call(this, a), this.requestUpdate(e, o, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? je;
  }
  static _$Ei() {
    if (this.hasOwnProperty(X("elementProperties"))) return;
    const e = bt(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(X("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(X("properties"))) {
      const s = this.properties, i = [...vt(s), ...$t(s)];
      for (const r of i) this.createProperty(r, s[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const s = litPropertyMetadata.get(e);
      if (s !== void 0) for (const [i, r] of s) this.elementProperties.set(i, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [s, i] of this.elementProperties) {
      const r = this._$Eu(s, i);
      r !== void 0 && this._$Eh.set(r, s);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const s = [];
    if (Array.isArray(e)) {
      const i = new Set(e.flat(1 / 0).reverse());
      for (const r of i) s.unshift(He(r));
    } else e !== void 0 && s.push(He(e));
    return s;
  }
  static _$Eu(e, s) {
    const i = s.attribute;
    return i === !1 ? void 0 : typeof i == "string" ? i : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var e;
    this._$ES = new Promise((s) => this.enableUpdating = s), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (e = this.constructor.l) == null || e.forEach((s) => s(this));
  }
  addController(e) {
    var s;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(e), this.renderRoot !== void 0 && this.isConnected && ((s = e.hostConnected) == null || s.call(e));
  }
  removeController(e) {
    var s;
    (s = this._$EO) == null || s.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), s = this.constructor.elementProperties;
    for (const i of s.keys()) this.hasOwnProperty(i) && (e.set(i, this[i]), delete this[i]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return ut(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((s) => {
      var i;
      return (i = s.hostConnected) == null ? void 0 : i.call(s);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((s) => {
      var i;
      return (i = s.hostDisconnected) == null ? void 0 : i.call(s);
    });
  }
  attributeChangedCallback(e, s, i) {
    this._$AK(e, i);
  }
  _$ET(e, s) {
    var n;
    const i = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, i);
    if (r !== void 0 && i.reflect === !0) {
      const a = (((n = i.converter) == null ? void 0 : n.toAttribute) !== void 0 ? i.converter : re).toAttribute(s, i.type);
      this._$Em = e, a == null ? this.removeAttribute(r) : this.setAttribute(r, a), this._$Em = null;
    }
  }
  _$AK(e, s) {
    var n, a;
    const i = this.constructor, r = i._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const o = i.getPropertyOptions(r), l = typeof o.converter == "function" ? { fromAttribute: o.converter } : ((n = o.converter) == null ? void 0 : n.fromAttribute) !== void 0 ? o.converter : re;
      this._$Em = r;
      const d = l.fromAttribute(s, o.type);
      this[r] = d ?? ((a = this._$Ej) == null ? void 0 : a.get(r)) ?? d, this._$Em = null;
    }
  }
  requestUpdate(e, s, i, r = !1, n) {
    var a;
    if (e !== void 0) {
      const o = this.constructor;
      if (r === !1 && (n = this[e]), i ?? (i = o.getPropertyOptions(e)), !((i.hasChanged ?? Pe)(n, s) || i.useDefault && i.reflect && n === ((a = this._$Ej) == null ? void 0 : a.get(e)) && !this.hasAttribute(o._$Eu(e, i)))) return;
      this.C(e, s, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, s, { useDefault: i, reflect: r, wrapped: n }, a) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, a ?? s ?? this[e]), n !== !0 || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (s = void 0), this._$AL.set(e, s)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (s) {
      Promise.reject(s);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var i;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [n, a] of this._$Ep) this[n] = a;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [n, a] of r) {
        const { wrapped: o } = a, l = this[n];
        o !== !0 || this._$AL.has(n) || l === void 0 || this.C(n, void 0, a, l);
      }
    }
    let e = !1;
    const s = this._$AL;
    try {
      e = this.shouldUpdate(s), e ? (this.willUpdate(s), (i = this._$EO) == null || i.forEach((r) => {
        var n;
        return (n = r.hostUpdate) == null ? void 0 : n.call(r);
      }), this.update(s)) : this._$EM();
    } catch (r) {
      throw e = !1, this._$EM(), r;
    }
    e && this._$AE(s);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    var s;
    (s = this._$EO) == null || s.forEach((i) => {
      var r;
      return (r = i.hostUpdated) == null ? void 0 : r.call(i);
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
    this._$Eq && (this._$Eq = this._$Eq.forEach((s) => this._$ET(s, this[s]))), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
U.elementStyles = [], U.shadowRootOptions = { mode: "open" }, U[X("elementProperties")] = /* @__PURE__ */ new Map(), U[X("finalized")] = /* @__PURE__ */ new Map(), pe == null || pe({ ReactiveElement: U }), (S.reactiveElementVersions ?? (S.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Z = globalThis, Ge = (t) => t, ne = Z.trustedTypes, Fe = ne ? ne.createPolicy("lit-html", { createHTML: (t) => t }) : void 0, et = "$lit$", C = `lit$${Math.random().toFixed(9).slice(2)}$`, tt = "?" + C, mt = `<${tt}>`, I = document, Q = () => I.createComment(""), ee = (t) => t === null || typeof t != "object" && typeof t != "function", ke = Array.isArray, xt = (t) => ke(t) || typeof (t == null ? void 0 : t[Symbol.iterator]) == "function", ue = `[ 	
\f\r]`, V = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, qe = /-->/g, Be = />/g, D = RegExp(`>|${ue}(?:([^\\s"'>=/]+)(${ue}*=${ue}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), We = /'/g, Ve = /"/g, st = /^(?:script|style|textarea|title)$/i, wt = (t) => (e, ...s) => ({ _$litType$: t, strings: e, values: s }), c = wt(1), j = Symbol.for("lit-noChange"), h = Symbol.for("lit-nothing"), Ye = /* @__PURE__ */ new WeakMap(), R = I.createTreeWalker(I, 129);
function it(t, e) {
  if (!ke(t) || !t.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Fe !== void 0 ? Fe.createHTML(e) : e;
}
const At = (t, e) => {
  const s = t.length - 1, i = [];
  let r, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", a = V;
  for (let o = 0; o < s; o++) {
    const l = t[o];
    let d, _, p = -1, g = 0;
    for (; g < l.length && (a.lastIndex = g, _ = a.exec(l), _ !== null); ) g = a.lastIndex, a === V ? _[1] === "!--" ? a = qe : _[1] !== void 0 ? a = Be : _[2] !== void 0 ? (st.test(_[2]) && (r = RegExp("</" + _[2], "g")), a = D) : _[3] !== void 0 && (a = D) : a === D ? _[0] === ">" ? (a = r ?? V, p = -1) : _[1] === void 0 ? p = -2 : (p = a.lastIndex - _[2].length, d = _[1], a = _[3] === void 0 ? D : _[3] === '"' ? Ve : We) : a === Ve || a === We ? a = D : a === qe || a === Be ? a = V : (a = D, r = void 0);
    const x = a === D && t[o + 1].startsWith("/>") ? " " : "";
    n += a === V ? l + mt : p >= 0 ? (i.push(d), l.slice(0, p) + et + l.slice(p) + C + x) : l + C + (p === -2 ? o : x);
  }
  return [it(t, n + (t[s] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class te {
  constructor({ strings: e, _$litType$: s }, i) {
    let r;
    this.parts = [];
    let n = 0, a = 0;
    const o = e.length - 1, l = this.parts, [d, _] = At(e, s);
    if (this.el = te.createElement(d, i), R.currentNode = this.el.content, s === 2 || s === 3) {
      const p = this.el.content.firstChild;
      p.replaceWith(...p.childNodes);
    }
    for (; (r = R.nextNode()) !== null && l.length < o; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const p of r.getAttributeNames()) if (p.endsWith(et)) {
          const g = _[a++], x = r.getAttribute(p).split(C), N = /([.?@])?(.*)/.exec(g);
          l.push({ type: 1, index: n, name: N[2], strings: x, ctor: N[1] === "." ? Pt : N[1] === "?" ? kt : N[1] === "@" ? Ct : de }), r.removeAttribute(p);
        } else p.startsWith(C) && (l.push({ type: 6, index: n }), r.removeAttribute(p));
        if (st.test(r.tagName)) {
          const p = r.textContent.split(C), g = p.length - 1;
          if (g > 0) {
            r.textContent = ne ? ne.emptyScript : "";
            for (let x = 0; x < g; x++) r.append(p[x], Q()), R.nextNode(), l.push({ type: 2, index: ++n });
            r.append(p[g], Q());
          }
        }
      } else if (r.nodeType === 8) if (r.data === tt) l.push({ type: 2, index: n });
      else {
        let p = -1;
        for (; (p = r.data.indexOf(C, p + 1)) !== -1; ) l.push({ type: 7, index: n }), p += C.length - 1;
      }
      n++;
    }
  }
  static createElement(e, s) {
    const i = I.createElement("template");
    return i.innerHTML = e, i;
  }
}
function G(t, e, s = t, i) {
  var a, o;
  if (e === j) return e;
  let r = i !== void 0 ? (a = s._$Co) == null ? void 0 : a[i] : s._$Cl;
  const n = ee(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== n && ((o = r == null ? void 0 : r._$AO) == null || o.call(r, !1), n === void 0 ? r = void 0 : (r = new n(t), r._$AT(t, s, i)), i !== void 0 ? (s._$Co ?? (s._$Co = []))[i] = r : s._$Cl = r), r !== void 0 && (e = G(t, r._$AS(t, e.values), r, i)), e;
}
class Et {
  constructor(e, s) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = s;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: s }, parts: i } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? I).importNode(s, !0);
    R.currentNode = r;
    let n = R.nextNode(), a = 0, o = 0, l = i[0];
    for (; l !== void 0; ) {
      if (a === l.index) {
        let d;
        l.type === 2 ? d = new se(n, n.nextSibling, this, e) : l.type === 1 ? d = new l.ctor(n, l.name, l.strings, this, e) : l.type === 6 && (d = new St(n, this, e)), this._$AV.push(d), l = i[++o];
      }
      a !== (l == null ? void 0 : l.index) && (n = R.nextNode(), a++);
    }
    return R.currentNode = I, r;
  }
  p(e) {
    let s = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, s), s += i.strings.length - 2) : i._$AI(e[s])), s++;
  }
}
class se {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, s, i, r) {
    this.type = 2, this._$AH = h, this._$AN = void 0, this._$AA = e, this._$AB = s, this._$AM = i, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const s = this._$AM;
    return s !== void 0 && (e == null ? void 0 : e.nodeType) === 11 && (e = s.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, s = this) {
    e = G(this, e, s), ee(e) ? e === h || e == null || e === "" ? (this._$AH !== h && this._$AR(), this._$AH = h) : e !== this._$AH && e !== j && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : xt(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== h && ee(this._$AH) ? this._$AA.nextSibling.data = e : this.T(I.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var n;
    const { values: s, _$litType$: i } = e, r = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = te.createElement(it(i.h, i.h[0]), this.options)), i);
    if (((n = this._$AH) == null ? void 0 : n._$AD) === r) this._$AH.p(s);
    else {
      const a = new Et(r, this), o = a.u(this.options);
      a.p(s), this.T(o), this._$AH = a;
    }
  }
  _$AC(e) {
    let s = Ye.get(e.strings);
    return s === void 0 && Ye.set(e.strings, s = new te(e)), s;
  }
  k(e) {
    ke(this._$AH) || (this._$AH = [], this._$AR());
    const s = this._$AH;
    let i, r = 0;
    for (const n of e) r === s.length ? s.push(i = new se(this.O(Q()), this.O(Q()), this, this.options)) : i = s[r], i._$AI(n), r++;
    r < s.length && (this._$AR(i && i._$AB.nextSibling, r), s.length = r);
  }
  _$AR(e = this._$AA.nextSibling, s) {
    var i;
    for ((i = this._$AP) == null ? void 0 : i.call(this, !1, !0, s); e !== this._$AB; ) {
      const r = Ge(e).nextSibling;
      Ge(e).remove(), e = r;
    }
  }
  setConnected(e) {
    var s;
    this._$AM === void 0 && (this._$Cv = e, (s = this._$AP) == null || s.call(this, e));
  }
}
class de {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, s, i, r, n) {
    this.type = 1, this._$AH = h, this._$AN = void 0, this.element = e, this.name = s, this._$AM = r, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = h;
  }
  _$AI(e, s = this, i, r) {
    const n = this.strings;
    let a = !1;
    if (n === void 0) e = G(this, e, s, 0), a = !ee(e) || e !== this._$AH && e !== j, a && (this._$AH = e);
    else {
      const o = e;
      let l, d;
      for (e = n[0], l = 0; l < n.length - 1; l++) d = G(this, o[i + l], s, l), d === j && (d = this._$AH[l]), a || (a = !ee(d) || d !== this._$AH[l]), d === h ? e = h : e !== h && (e += (d ?? "") + n[l + 1]), this._$AH[l] = d;
    }
    a && !r && this.j(e);
  }
  j(e) {
    e === h ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Pt extends de {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === h ? void 0 : e;
  }
}
class kt extends de {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== h);
  }
}
class Ct extends de {
  constructor(e, s, i, r, n) {
    super(e, s, i, r, n), this.type = 5;
  }
  _$AI(e, s = this) {
    if ((e = G(this, e, s, 0) ?? h) === j) return;
    const i = this._$AH, r = e === h && i !== h || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, n = e !== h && (i === h || r);
    r && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var s;
    typeof this._$AH == "function" ? this._$AH.call(((s = this.options) == null ? void 0 : s.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class St {
  constructor(e, s, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = s, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    G(this, e);
  }
}
const _e = Z.litHtmlPolyfillSupport;
_e == null || _e(te, se), (Z.litHtmlVersions ?? (Z.litHtmlVersions = [])).push("3.3.3");
const Tt = (t, e, s) => {
  const i = (s == null ? void 0 : s.renderBefore) ?? e;
  let r = i._$litPart$;
  if (r === void 0) {
    const n = (s == null ? void 0 : s.renderBefore) ?? null;
    i._$litPart$ = r = new se(e.insertBefore(Q(), n), n, void 0, s ?? {});
  }
  return r._$AI(t), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const z = globalThis;
let E = class extends U {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var s;
    const e = super.createRenderRoot();
    return (s = this.renderOptions).renderBefore ?? (s.renderBefore = e.firstChild), e;
  }
  update(e) {
    const s = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Tt(s, this.renderRoot, this.renderOptions);
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
    return j;
  }
};
var Je;
E._$litElement$ = !0, E.finalized = !0, (Je = z.litElementHydrateSupport) == null || Je.call(z, { LitElement: E });
const ge = z.litElementPolyfillSupport;
ge == null || ge({ LitElement: E });
(z.litElementVersions ?? (z.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const B = (t) => (e, s) => {
  s !== void 0 ? s.addInitializer(() => {
    customElements.define(t, e);
  }) : customElements.define(t, e);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Mt = { attribute: !0, type: String, converter: re, reflect: !1, hasChanged: Pe }, Ot = (t = Mt, e, s) => {
  const { kind: i, metadata: r } = s;
  let n = globalThis.litPropertyMetadata.get(r);
  if (n === void 0 && globalThis.litPropertyMetadata.set(r, n = /* @__PURE__ */ new Map()), i === "setter" && ((t = Object.create(t)).wrapped = !0), n.set(s.name, t), i === "accessor") {
    const { name: a } = s;
    return { set(o) {
      const l = e.get.call(this);
      e.set.call(this, o), this.requestUpdate(a, l, t, !0, o);
    }, init(o) {
      return o !== void 0 && this.C(a, void 0, t, o), o;
    } };
  }
  if (i === "setter") {
    const { name: a } = s;
    return function(o) {
      const l = this[a];
      e.call(this, o), this.requestUpdate(a, l, t, !0, o);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function f(t) {
  return (e, s) => typeof s == "object" ? Ot(t, e, s) : ((i, r, n) => {
    const a = r.hasOwnProperty(n);
    return r.constructor.createProperty(n, i), a ? Object.getOwnPropertyDescriptor(r, n) : void 0;
  })(t, e, s);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function u(t) {
  return f({ ...t, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Dt = (t) => t.strings === void 0;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Rt = { CHILD: 2 }, zt = (t) => (...e) => ({ _$litDirective$: t, values: e });
class It {
  constructor(e) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(e, s, i) {
    this._$Ct = e, this._$AM = s, this._$Ci = i;
  }
  _$AS(e, s) {
    return this.update(e, s);
  }
  update(e, s) {
    return this.render(...s);
  }
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const K = (t, e) => {
  var i;
  const s = t._$AN;
  if (s === void 0) return !1;
  for (const r of s) (i = r._$AO) == null || i.call(r, e, !1), K(r, e);
  return !0;
}, ae = (t) => {
  let e, s;
  do {
    if ((e = t._$AM) === void 0) break;
    s = e._$AN, s.delete(t), t = e;
  } while ((s == null ? void 0 : s.size) === 0);
}, rt = (t) => {
  for (let e; e = t._$AM; t = e) {
    let s = e._$AN;
    if (s === void 0) e._$AN = s = /* @__PURE__ */ new Set();
    else if (s.has(t)) break;
    s.add(t), Ht(e);
  }
};
function Nt(t) {
  this._$AN !== void 0 ? (ae(this), this._$AM = t, rt(this)) : this._$AM = t;
}
function Ut(t, e = !1, s = 0) {
  const i = this._$AH, r = this._$AN;
  if (r !== void 0 && r.size !== 0) if (e) if (Array.isArray(i)) for (let n = s; n < i.length; n++) K(i[n], !1), ae(i[n]);
  else i != null && (K(i, !1), ae(i));
  else K(this, t);
}
const Ht = (t) => {
  t.type == Rt.CHILD && (t._$AP ?? (t._$AP = Ut), t._$AQ ?? (t._$AQ = Nt));
};
class Lt extends It {
  constructor() {
    super(...arguments), this._$AN = void 0;
  }
  _$AT(e, s, i) {
    super._$AT(e, s, i), rt(this), this.isConnected = e._$AU;
  }
  _$AO(e, s = !0) {
    var i, r;
    e !== this.isConnected && (this.isConnected = e, e ? (i = this.reconnected) == null || i.call(this) : (r = this.disconnected) == null || r.call(this)), s && (K(this, e), ae(this));
  }
  setValue(e) {
    if (Dt(this._$Ct)) this._$Ct._$AI(e, this);
    else {
      const s = [...this._$Ct._$AH];
      s[this._$Ci] = e, this._$Ct._$AI(s, this, 0);
    }
  }
  disconnected() {
  }
  reconnected() {
  }
}
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const jt = () => new Gt();
class Gt {
}
const fe = /* @__PURE__ */ new WeakMap(), Ft = zt(class extends Lt {
  render(t) {
    return h;
  }
  update(t, [e]) {
    var i;
    const s = e !== this.G;
    return s && this.rt(void 0), (s || this.lt !== this.ct) && (this.G = e, this.ht = (i = t.options) == null ? void 0 : i.host, this.rt(this.ct = t.element)), h;
  }
  rt(t) {
    if (this.G !== void 0) if (this.isConnected || (t = void 0), typeof this.G == "function") {
      const e = this.ht ?? globalThis;
      let s = fe.get(e);
      s === void 0 && (s = /* @__PURE__ */ new WeakMap(), fe.set(e, s)), s.get(this.G) !== void 0 && this.G.call(this.ht, void 0), s.set(this.G, t), t !== void 0 && this.G.call(this.ht, t);
    } else this.G.value = t;
  }
  get lt() {
    var t, e;
    return typeof this.G == "function" ? (t = fe.get(this.ht ?? globalThis)) == null ? void 0 : t.get(this.G) : (e = this.G) == null ? void 0 : e.value;
  }
  disconnected() {
    this.lt === this.ct && this.rt(void 0);
  }
  reconnected() {
    this.rt(this.ct);
  }
});
function w(t, e) {
  return t.connection.sendMessagePromise(e);
}
const qt = (t) => w(t, { type: "dash480/panels/list" }), nt = (t, e) => w(t, {
  type: "dash480/pages/list",
  panel_entry_id: e
}), Bt = (t, e, s, i, r) => w(t, {
  type: "dash480/pages/create",
  panel_entry_id: e,
  title: s,
  columns: i,
  rows: r
}), Wt = (t, e, s) => w(t, { type: "dash480/pages/update", page_id: e, ...s }), Vt = (t, e) => w(t, { type: "dash480/pages/delete", page_id: e }), Yt = (t, e) => w(t, {
  type: "dash480/pages/publish",
  panel_entry_id: e
}), Xt = (t, e) => w(t, {
  type: "dash480/preview/render",
  page_draft: e
}), Zt = 1e4, ve = /* @__PURE__ */ new Map(), ye = (t, e) => {
  const s = ve.get(e);
  if (s && Date.now() - s.at < Zt) return s.result;
  const i = w(t, {
    type: "dash480/registry/compatible_entities",
    tile_type: e
  });
  return ve.set(e, { at: Date.now(), result: i }), i.catch(() => ve.delete(e)), i;
};
let Y = null;
const Kt = (t) => (Y || (Y = w(t, { type: "dash480/registry/icons" }), Y.catch(() => Y = null)), Y), Jt = (t) => w(t, { type: "dash480/registry/areas" }), Qt = (t, e, s, i, r) => w(t, {
  type: "dash480/pages/generate_from_area",
  panel_entry_id: e,
  area_id: s,
  mode: i,
  ...r ? { target_page_id: r } : {}
}), J = 24, oe = 24, le = 20, ce = 80, at = 430, Ce = 480, $e = 24;
function ot(t, e) {
  return {
    colW: (Ce - 2 * J - (t - 1) * oe) / t,
    rowH: (at - ce - (e - 1) * le) / e
  };
}
function es(t, e, s, i) {
  return me(t, e, s, i, 1, 1);
}
function me(t, e, s, i, r, n) {
  const { colW: a, rowH: o } = ot(t, e);
  return {
    x: J + i * (a + oe),
    y: ce + s * (o + le),
    w: a * n + oe * (n - 1),
    h: o * r + le * (r - 1)
  };
}
function Xe(t, e, s, i) {
  if (i < ce - 10 || i > at + 10 || s < J - 10 || s > Ce - J + 10) return null;
  const { colW: n, rowH: a } = ot(t, e), o = Math.max(0, Math.min(t - 1, Math.floor((s - J) / (n + oe))));
  return { row: Math.max(0, Math.min(e - 1, Math.floor((i - ce) / (a + le)))), col: o };
}
function H(t, e) {
  const s = /* @__PURE__ */ new Set();
  for (const i of t) {
    if (i.id === e) continue;
    const r = i.rs ?? 1, n = i.cs ?? 1;
    for (let a = i.row; a < i.row + r; a++)
      for (let o = i.col; o < i.col + n; o++)
        s.add(`${a},${o}`);
  }
  return s;
}
function L(t, e, s, i, r, n, a) {
  if (t < 0 || e < 0 || t + s > r || e + i > n) return !1;
  for (let o = t; o < t + s; o++)
    for (let l = e; l < e + i; l++)
      if (a.has(`${o},${l}`)) return !1;
  return !0;
}
const xe = Ce;
var ts = Object.defineProperty, ss = Object.getOwnPropertyDescriptor, W = (t, e, s, i) => {
  for (var r = i > 1 ? void 0 : i ? ss(e, s) : e, n = t.length - 1, a; n >= 0; n--)
    (a = t[n]) && (r = (i ? a(e, s, r) : a(r)) || r);
  return i && r && ts(e, s, r), r;
};
const is = { green: "#43A047", yellow: "#FFA600", red: "#DB4437" }, Ze = "#FFFFFF", Ke = "#111827", we = 270, rs = 225;
function ns(t, e, s) {
  if (!t || !(s > e)) return [];
  const i = [];
  for (const n of ["green", "yellow", "red"]) {
    const a = t[n];
    typeof a == "number" && Number.isFinite(a) && i.push({ key: n, level: a });
  }
  i.sort((n, a) => n.level - a.level);
  const r = [];
  for (let n = 0; n < i.length; n++) {
    const a = Math.min(s, Math.max(e, i[n].level)), o = n + 1 < i.length ? Math.min(s, Math.max(e, i[n + 1].level)) : s;
    o > a && r.push({ color: is[i[n].key], start: a, end: o });
  }
  return r;
}
function as(t, e, s) {
  const i = s - e, r = [];
  let n = 0;
  for (const a of t) {
    const o = (a.start - e) / i * we, l = (a.end - e) / i * we;
    o > n + 0.05 && r.push(`transparent ${n}deg ${o}deg`), r.push(`${a.color} ${o}deg ${l}deg`), n = l;
  }
  return n < 360 && r.push(`transparent ${n}deg 360deg`), `conic-gradient(from ${rs}deg, ${r.join(", ")})`;
}
function os(t, e, s) {
  const i = s - e;
  return (135 + (i > 0 ? Math.min(1, Math.max(0, (t - e) / i)) : 0) * we) % 360 - 270;
}
const ls = 5;
let T = class extends E {
  constructor() {
    super(...arguments), this.previewTiles = [], this.selection = { kind: "none" }, this._drag = null, this._now = /* @__PURE__ */ new Date(), this._clockTimer = null;
  }
  _emit(t, e) {
    this.dispatchEvent(new CustomEvent(t, { detail: e, bubbles: !0, composed: !0 }));
  }
  _onTilePointerDown(t, e, s) {
    if (t.button !== 0) return;
    t.stopPropagation();
    const i = this.page.tiles.find((o) => o.id === e.id);
    if (!i) return;
    const r = this.shadowRoot.querySelector(".device").getBoundingClientRect(), n = t.clientX - r.left, a = t.clientY - r.top;
    this._drag = {
      tileId: e.id,
      mode: s,
      grabDx: n - e.x,
      grabDy: a - e.y,
      startX: n,
      startY: a,
      active: !1,
      ghost: null,
      canvasLeft: r.left,
      canvasTop: r.top,
      tile: i,
      occupied: H(this.page.tiles, i.id)
    }, t.currentTarget.setPointerCapture(t.pointerId);
  }
  _onPointerMove(t) {
    const e = this._drag;
    if (!e) return;
    const s = { x: t.clientX - e.canvasLeft, y: t.clientY - e.canvasTop };
    if (!e.active) {
      if (Math.hypot(s.x - e.startX, s.y - e.startY) < ls) return;
      e.active = !0;
    }
    const { tile: i, occupied: r } = e, { rows: n, columns: a } = this.page;
    let o = null;
    if (e.mode === "move") {
      const l = Xe(a, n, s.x - e.grabDx, s.y - e.grabDy);
      if (l) {
        const d = i.rs ?? 1, _ = i.cs ?? 1;
        o = {
          ...l,
          rs: d,
          cs: _,
          rect: me(a, n, l.row, l.col, d, _),
          valid: L(l.row, l.col, d, _, n, a, r)
        };
      }
    } else {
      const l = Xe(a, n, s.x, s.y);
      if (l) {
        const d = Math.max(1, l.row - i.row + 1), _ = Math.max(1, l.col - i.col + 1);
        o = {
          row: i.row,
          col: i.col,
          rs: d,
          cs: _,
          rect: me(a, n, i.row, i.col, d, _),
          valid: L(i.row, i.col, d, _, n, a, r)
        };
      }
    }
    this._drag = { ...e, ghost: o };
  }
  _onPointerUp() {
    const t = this._drag;
    if (!t) return;
    if (this._drag = null, !t.active) {
      this._emit("tile-selected", { tileId: t.tileId });
      return;
    }
    const e = t.ghost;
    if (!e || !e.valid) return;
    const s = t.tile;
    t.mode === "move" ? (e.row !== s.row || e.col !== s.col) && this._emit("tile-moved", { tileId: s.id, row: e.row, col: e.col }) : (e.rs !== (s.rs ?? 1) || e.cs !== (s.cs ?? 1)) && this._emit("tile-resized", { tileId: s.id, rs: e.rs, cs: e.cs });
  }
  _onPointerCancel() {
    this._drag = null;
  }
  render() {
    var a, o;
    if (!this.page) return h;
    const t = this.page, e = H(t.tiles), s = [];
    for (let l = 0; l < t.rows; l++)
      for (let d = 0; d < t.columns; d++)
        e.has(`${l},${d}`) || s.push({ row: l, col: d, rect: es(t.columns, t.rows, l, d) });
    const i = this.selection.kind === "tile" ? this.selection.tileId : null, r = (a = this._drag) != null && a.active ? this._drag.tileId : null, n = (o = this._drag) != null && o.active ? this._drag.ghost : null;
    return c`
      <div
        class="device"
        style="width:${xe}px;height:${xe}px;"
        @click=${() => this._emit("selection-cleared")}
        @pointermove=${this._onPointerMove}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerCancel}
      >
        ${s.map(
      (l) => c`
            <div
              class="cell ${this.selection.kind === "cell" && this.selection.row === l.row && this.selection.col === l.col ? "selected" : ""}"
              style="left:${l.rect.x}px;top:${l.rect.y}px;width:${l.rect.w}px;height:${l.rect.h}px;"
              @click=${(d) => {
        d.stopPropagation(), this._emit("cell-selected", { row: l.row, col: l.col });
      }}
            >
              <span class="plus">+</span>
            </div>
          `
    )}
        ${this.previewTiles.map((l) => this._renderTile(l, l.id === i, l.id === r))}
        ${n ? c`
              <div
                class="ghost ${n.valid ? "valid" : "invalid"}"
                style="left:${n.rect.x}px;top:${n.rect.y}px;width:${n.rect.w}px;height:${n.rect.h}px;"
              ></div>
            ` : h}
      </div>
    `;
  }
  _renderTile(t, e, s) {
    var Me, Oe, De, Re, ze, Ie, Ne;
    const i = this.page.tiles.find(($) => $.id === t.id);
    if (!i) return h;
    const r = i.type === "gauge", n = i.type === "weather", a = (Me = i.entity_id) == null ? void 0 : Me.startsWith("camera."), o = ((Oe = i.entity_id) == null ? void 0 : Oe.toLowerCase().includes("battery")) || ((De = t.friendly_name) == null ? void 0 : De.toLowerCase().includes("battery")), l = i.type === "clock";
    let d = 0, _ = [], p = 0, g = 100, x = -135;
    if (r) {
      p = i.min ?? 0, g = i.max ?? 100, g <= p && (g = p + 1);
      const $ = Number(t.state), O = !Number.isNaN($);
      O && g > p && (d = Math.max(0, Math.min(100, ($ - p) / (g - p) * 100))), _ = ns(i.severity, p, g), x = os(O ? $ : p, p, g);
    }
    const N = typeof ((Re = t.attributes) == null ? void 0 : Re.unit_of_measurement) == "string" ? t.attributes.unit_of_measurement : "", lt = t.state == null || t.state === "" || t.state === "unknown" || t.state === "unavailable" ? "--" : `${t.state}${N}`, Se = (ze = t.attributes) == null ? void 0 : ze.temperature, ct = ((Ie = t.attributes) == null ? void 0 : Ie.temperature_unit) ?? "", Te = !i.entity_id;
    return c`
      <div
        class="tile ${e ? "selected" : ""} ${s ? "dragging" : ""} ${Te ? "missing" : ""}"
        style="left:${t.x}px;top:${t.y}px;width:${t.w}px;height:${t.h}px;"
        @pointerdown=${($) => this._onTilePointerDown($, t, "move")}
        @click=${($) => $.stopPropagation()}
      >
        ${Te ? c`<div class="tile-missing-label">No entity —<br />select one</div>` : c`
              <div class="tile-label">${t.friendly_name}</div>
              ${r ? _.length ? c`
                      <div class="gauge-wrap">
                        <div class="gauge-face" style="background: ${as(_, p, g)}"></div>
                        <div class="gauge-needle" style="transform: rotate(${x}deg); background: ${Ke}">
                          <div class="gauge-needle-core" style="background: ${Ze}"></div>
                        </div>
                        <div class="gauge-hub" style="background: ${Ze}; box-shadow: 0 0 0 2px ${Ke}"></div>
                        <div class="gauge-value">${lt}</div>
                      </div>
                    ` : c`
                      <div class="gauge-ring" style="background: conic-gradient(#38bdf8 ${d * 3.6}deg, #334155 0deg);">
                        <div class="gauge-ring-inner">${t.state ?? "--"}</div>
                      </div>
                    ` : n ? c`
                      <div class="weather-condition">${t.state ?? "--"}</div>
                      <div class="tile-state">${Se !== void 0 ? `${Se}${ct}` : "--"}</div>
                    ` : a && ((Ne = t.attributes) != null && Ne.entity_picture) ? c`
                        <img
                          src="${t.attributes.entity_picture}"
                          style="width: 100%; height: calc(100% - 30px); object-fit: contain; margin-top: 4px;"
                          draggable="false"
                        />
                      ` : o ? (() => {
      const $ = parseInt(t.state ?? "", 10) || 50, O = Math.max(0, Math.min(100, $)), dt = Math.round(O / 100 * 42), ht = O < 15 ? "#EF4444" : O < 50 ? "#F59E0B" : "#10B981";
      return c`
                            <div class="battery-preview-container" style="display: flex; align-items: center; justify-content: center; gap: 12px; height: calc(100% - 30px); margin-top: 4px;">
                              <div class="battery-outline" style="position: relative; width: 48px; height: 24px; border: 2px solid #e2e8f0; border-radius: 4px; box-sizing: border-box; display: flex; align-items: center; padding: 1px;">
                                <div class="battery-bar" style="width: ${dt}px; height: 100%; background-color: ${ht}; border-radius: 2px; transition: width 0.2s ease;"></div>
                                <div class="battery-cap" style="position: absolute; right: -6px; top: 5px; width: 4px; height: 10px; background-color: #e2e8f0; border-radius: 1px;"></div>
                              </div>
                              <div class="battery-text" style="font-size: 20px; font-weight: bold; color: #e2e8f0;">${O}%</div>
                            </div>
                          `;
    })() : l ? c`
                            <div class="clock-time" style="font-size: 24px; font-weight: bold; text-align: center; margin-top: 8px;">
                              ${this._now.getHours().toString().padStart(2, "0")}:${this._now.getMinutes().toString().padStart(2, "0")}
                            </div>
                          ` : c`<div class="tile-state">${t.state ?? "--"}</div>`}
            `}
        ${e ? c`
              <div
                class="resize-handle"
                title="Drag to resize"
                @pointerdown=${($) => this._onTilePointerDown($, t, "resize")}
              ></div>
            ` : h}
      </div>
    `;
  }
  connectedCallback() {
    super.connectedCallback(), this._clockTimer = setInterval(() => {
      this._now = /* @__PURE__ */ new Date(), this.requestUpdate();
    }, 1e3);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._clockTimer && clearInterval(this._clockTimer);
  }
};
T.styles = q`
    :host {
      display: block;
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
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .cell .plus {
      opacity: 0;
      font-size: 20px;
      color: rgba(255, 255, 255, 0.5);
    }
    .cell:hover {
      background: rgba(255, 255, 255, 0.08);
    }
    .cell:hover .plus {
      opacity: 1;
    }
    .cell.selected {
      border-color: var(--primary-color, #38bdf8);
      border-style: solid;
    }
    .tile {
      position: absolute;
      background: #1e293b;
      border-radius: 10px;
      color: #e5e7eb;
      padding: 6px;
      box-sizing: border-box;
      cursor: grab;
      touch-action: none;
      user-select: none;
      -webkit-user-select: none;
    }
    .tile.selected {
      outline: 2px solid var(--primary-color, #38bdf8);
    }
    .tile.dragging {
      opacity: 0.4;
    }
    .tile.missing {
      border: 1px dashed rgba(255, 255, 255, 0.3);
      background: rgba(30, 41, 59, 0.5);
    }
    .tile-missing-label {
      font-size: 11px;
      opacity: 0.6;
      text-align: center;
      margin-top: 12px;
      line-height: 1.4;
    }
    .tile-label {
      font-size: 11px;
      opacity: 0.7;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
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
    .gauge-ring {
      width: 60%;
      max-width: 80px;
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
    .gauge-wrap {
      position: relative;
      width: 74%;
      max-width: 96px;
      aspect-ratio: 1;
      margin: 4px auto 0;
    }
    .gauge-face {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      -webkit-mask: radial-gradient(circle, transparent 52%, #000 53%);
      mask: radial-gradient(circle, transparent 52%, #000 53%);
    }
    .gauge-needle {
      position: absolute;
      left: 50%;
      bottom: 50%;
      width: 12px;
      height: 50%;
      margin-left: -6px;
      border-radius: 6px;
      transform-origin: center bottom;
      z-index: 1;
    }
    .gauge-needle-core {
      position: absolute;
      left: 2px;
      right: 2px;
      top: 2px;
      bottom: 0;
      border-radius: 4px;
    }
    .gauge-hub {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 8px;
      height: 8px;
      margin-left: -4px;
      margin-top: -4px;
      border-radius: 50%;
      z-index: 2;
    }
    .gauge-value {
      position: absolute;
      left: 0;
      right: 0;
      top: 60%;
      text-align: center;
      font-size: 11px;
      line-height: 1.2;
      z-index: 3;
    }
    .resize-handle {
      position: absolute;
      right: 0;
      bottom: 0;
      width: 14px;
      height: 14px;
      cursor: nwse-resize;
      border-right: 3px solid var(--primary-color, #38bdf8);
      border-bottom: 3px solid var(--primary-color, #38bdf8);
      border-bottom-right-radius: 8px;
    }
    .ghost {
      position: absolute;
      border-radius: 10px;
      pointer-events: none;
      box-sizing: border-box;
    }
    .ghost.valid {
      border: 2px solid #4ade80;
      background: rgba(74, 222, 128, 0.12);
    }
    .ghost.invalid {
      border: 2px solid #f87171;
      background: rgba(248, 113, 113, 0.12);
    }
  `;
W([
  f({ attribute: !1 })
], T.prototype, "page", 2);
W([
  f({ attribute: !1 })
], T.prototype, "previewTiles", 2);
W([
  f({ attribute: !1 })
], T.prototype, "selection", 2);
W([
  u()
], T.prototype, "_drag", 2);
W([
  u()
], T.prototype, "_now", 2);
T = W([
  B("dash480-preview-canvas")
], T);
var cs = Object.defineProperty, ds = Object.getOwnPropertyDescriptor, M = (t, e, s, i) => {
  for (var r = i > 1 ? void 0 : i ? ds(e, s) : e, n = t.length - 1, a; n >= 0; n--)
    (a = t[n]) && (r = (i ? a(e, s, r) : a(r)) || r);
  return i && r && cs(e, s, r), r;
};
let P = class extends E {
  constructor() {
    super(...arguments), this.tileType = "entity", this._entities = [], this._open = !1, this._search = "", this._loadedType = null;
  }
  willUpdate(t) {
    if (this.hass && this.tileType !== this._loadedType) {
      const e = this.tileType;
      this._loadedType = e, ye(this.hass, e).then((s) => {
        this._loadedType === e && (this._entities = s.entities);
      });
    }
  }
  _filtered() {
    const t = this._search.trim().toLowerCase();
    return t ? this._entities.filter(
      (e) => e.friendly_name.toLowerCase().includes(t) || e.entity_id.toLowerCase().includes(t)
    ) : this._entities;
  }
  _pick(t) {
    this._open = !1, this._search = "", this.dispatchEvent(new CustomEvent("entity-selected", { detail: { entity: t }, bubbles: !0, composed: !0 }));
  }
  _toggle() {
    this._open = !this._open, this._open && this.updateComplete.then(() => {
      var t, e;
      (e = (t = this.shadowRoot) == null ? void 0 : t.querySelector(".search")) == null || e.focus();
    });
  }
  render() {
    const t = this.value ? this._entities.find((s) => s.entity_id === this.value) : void 0, e = (t == null ? void 0 : t.friendly_name) ?? this.value ?? "Choose an entity…";
    return c`
      <button class="current ${this.value ? "" : "placeholder"}" @click=${this._toggle}>
        <span class="name">${e}</span>
        ${this.value ? c`<span class="id">${this.value}</span>` : h}
        <span class="chevron">${this._open ? "▴" : "▾"}</span>
      </button>
      ${this.warning ? c`<div class="warning">⚠ ${this.warning}</div>` : h}
      ${this._open ? c`
            <div class="dropdown">
              <input
                class="search"
                placeholder="Search entities…"
                .value=${this._search}
                @input=${(s) => this._search = s.target.value}
              />
              <div class="list">
                ${this._filtered().length === 0 ? c`<div class="empty">No matching entities</div>` : this._filtered().map(
      (s) => c`
                        <button
                          class="row ${s.entity_id === this.value ? "selected" : ""}"
                          @click=${() => this._pick(s)}
                        >
                          <span class="name">${s.friendly_name}</span>
                          <span class="id">${s.entity_id}</span>
                        </button>
                      `
    )}
              </div>
            </div>
          ` : h}
    `;
  }
};
P.styles = q`
    :host {
      display: block;
      position: relative;
    }
    .current {
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 2px;
      padding: 8px 10px;
      border: 1px solid #555;
      border-radius: 6px;
      background: transparent;
      color: inherit;
      cursor: pointer;
      text-align: left;
      position: relative;
    }
    .current:hover {
      border-color: #888;
    }
    .current.placeholder .name {
      opacity: 0.6;
    }
    .chevron {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      opacity: 0.6;
      font-size: 11px;
    }
    .name {
      font-size: 14px;
    }
    .id {
      font-size: 11px;
      opacity: 0.6;
    }
    .warning {
      margin-top: 4px;
      font-size: 12px;
      color: #fbbf24;
    }
    .dropdown {
      position: absolute;
      top: calc(100% + 4px);
      left: 0;
      right: 0;
      z-index: 10;
      background: var(--card-background-color, #1e1e1e);
      border: 1px solid #555;
      border-radius: 6px;
      padding: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
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
      max-height: 240px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .row {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      padding: 6px 8px;
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
    .row.selected {
      background: rgba(56, 189, 248, 0.15);
    }
    .empty {
      padding: 12px;
      text-align: center;
      opacity: 0.6;
      font-size: 13px;
    }
  `;
M([
  f({ attribute: !1 })
], P.prototype, "hass", 2);
M([
  f()
], P.prototype, "tileType", 2);
M([
  f()
], P.prototype, "value", 2);
M([
  f()
], P.prototype, "warning", 2);
M([
  u()
], P.prototype, "_entities", 2);
M([
  u()
], P.prototype, "_open", 2);
M([
  u()
], P.prototype, "_search", 2);
P = M([
  B("dash480-entity-select")
], P);
var hs = Object.defineProperty, ps = Object.getOwnPropertyDescriptor, k = (t, e, s, i) => {
  for (var r = i > 1 ? void 0 : i ? ps(e, s) : e, n = t.length - 1, a; n >= 0; n--)
    (a = t[n]) && (r = (i ? a(e, s, r) : a(r)) || r);
  return i && r && hs(e, s, r), r;
};
function be(t) {
  switch (t.unit_of_measurement) {
    case "%":
      return { min: 0, max: 100 };
    case "°C":
      return { min: 0, max: 40 };
    case "°F":
      return { min: 32, max: 100 };
    case "W":
      return { min: 0, max: 1e3 };
    case "kW":
      return { min: 0, max: 10 };
  }
  switch (t.device_class) {
    case "battery":
    case "humidity":
      return { min: 0, max: 100 };
    case "temperature":
      return { min: 0, max: 40 };
  }
  return { min: 0, max: 100 };
}
const us = (t) => t.replace(/\s*\([0-9A-F]+\)\s*$/i, "");
let y = class extends E {
  constructor() {
    super(...arguments), this.selection = { kind: "none" }, this._addType = "entity", this._icons = [], this._compatible = null, this._shrinkError = "", this._rangeError = "", this._addError = "", this._compatSeq = 0;
  }
  connectedCallback() {
    super.connectedCallback(), Kt(this.hass).then((t) => this._icons = t.icons);
  }
  willUpdate(t) {
    if (t.has("selection")) {
      this._shrinkError = "", this._rangeError = "", this._addError = "";
      const e = this._selectedTile();
      e && (this._compatible = null, this._loadCompatible(e.type));
    }
  }
  _loadCompatible(t) {
    const e = ++this._compatSeq;
    ye(this.hass, t).then((s) => {
      e === this._compatSeq && (this._compatible = s.entities);
    });
  }
  _selectedTile() {
    if (this.selection.kind !== "tile") return;
    const t = this.selection.tileId;
    return this.page.tiles.find((e) => e.id === t);
  }
  _emit(t, e) {
    this.dispatchEvent(new CustomEvent(t, { detail: e, bubbles: !0, composed: !0 }));
  }
  // ---------- Mode A: page settings ----------
  _changeGrid(t, e) {
    const s = e.target, i = Number(s.value), r = t === "rows" ? i : this.page.rows, n = t === "columns" ? i : this.page.columns, a = this.page.tiles.filter(
      (o) => o.row + (o.rs ?? 1) > r || o.col + (o.cs ?? 1) > n
    );
    if (a.length) {
      const o = a.map((l) => l.entity_id ?? l.id).join(", ");
      this._shrinkError = `${a.length} tile${a.length > 1 ? "s" : ""} won't fit in a ${r}×${n} grid — move or remove first: ${o}`, s.value = String(this.page[t]);
      return;
    }
    this._shrinkError = "", this._emit("page-changed", { [t]: i });
  }
  _renderPageSettings() {
    const t = this.page;
    return c`
      <h3>Page settings</h3>
      <label class="field">
        <span>Title</span>
        <input
          .value=${t.title}
          @change=${(e) => this._emit("page-changed", { title: e.target.value })}
        />
      </label>
      <div class="row2">
        <label class="field">
          <span>Rows</span>
          <select @change=${(e) => this._changeGrid("rows", e)}>
            ${[1, 2, 3, 4, 5, 6].map((e) => c`<option value=${e} ?selected=${e === t.rows}>${e}</option>`)}
          </select>
        </label>
        <label class="field">
          <span>Columns</span>
          <select @change=${(e) => this._changeGrid("columns", e)}>
            ${[1, 2, 3, 4, 5, 6].map((e) => c`<option value=${e} ?selected=${e === t.columns}>${e}</option>`)}
          </select>
        </label>
      </div>
      ${this._shrinkError ? c`<div class="error">${this._shrinkError}</div>` : h}
      <div class="meta">${t.tiles.length} / ${$e} tiles</div>
      <div class="hint">Click a tile to edit it, or an empty cell to add one. Drag tiles to move them.</div>
    `;
  }
  // ---------- Mode B: add tile ----------
  _addClockTile() {
    if (this.selection.kind !== "cell") return;
    const { row: t, col: e } = this.selection;
    if (!L(t, e, 1, 1, this.page.rows, this.page.columns, H(this.page.tiles))) {
      this._addError = "That cell is now occupied — pick another cell.";
      return;
    }
    this._addError = "";
    const s = {
      id: `t${Date.now()}_${Math.floor(Math.random() * 1e3)}`,
      type: "clock",
      row: t,
      col: e,
      rs: 1,
      cs: 1
    };
    this._emit("tile-added", { tile: s });
  }
  _onAddEntityPicked(t) {
    if (this.selection.kind !== "cell") return;
    const { row: e, col: s } = this.selection;
    if (!L(e, s, 1, 1, this.page.rows, this.page.columns, H(this.page.tiles))) {
      this._addError = "That cell is now occupied — pick another cell.";
      return;
    }
    this._addError = "";
    const i = t.detail.entity, r = {
      id: `t${Date.now()}_${Math.floor(Math.random() * 1e3)}`,
      type: this._addType,
      entity_id: i.entity_id,
      row: e,
      col: s,
      rs: 1,
      cs: 1,
      ...this._addType === "gauge" ? be(i) : {}
    };
    this._emit("tile-added", { tile: r });
  }
  _renderAddForm() {
    if (this.page.tiles.length >= $e)
      return c`
        <h3>Add tile</h3>
        <div class="error">Page is full (${$e} tiles max). Remove a tile first.</div>
      `;
    const t = this.selection;
    return c`
      <h3>Add tile</h3>
      <div class="meta">Row ${t.row + 1}, column ${t.col + 1}</div>
      ${this._renderTypeButtons(this._addType, (e) => this._addType = e)}
      ${this._addType !== "clock" ? c`
        <label class="field">
          <span>Entity</span>
          <dash480-entity-select
            .hass=${this.hass}
            .tileType=${this._addType}
            @entity-selected=${this._onAddEntityPicked}
          >
          </dash480-entity-select>
        </label>
        ${this._addError ? c`<div class="error">${this._addError}</div>` : h}
      ` : c`<button class="submit" @click=${this._addClockTile}>Add clock</button>`}
      <div class="hint">${this._addType === "clock" ? "The clock tile has no settings." : "The tile is added as soon as you pick an entity — you can adjust everything afterwards."}</div>
    `;
  }
  _renderTypeButtons(t, e) {
    return c`
      <div class="segmented">
        ${[
      { value: "entity", label: "Entity" },
      { value: "gauge", label: "Gauge" },
      { value: "weather", label: "Weather" },
      { value: "clock", label: "Clock" }
    ].map(
      (i) => c`
            <button class=${i.value === t ? "active" : ""} @click=${() => e(i.value)}>
              ${i.label}
            </button>
          `
    )}
      </div>
    `;
  }
  // ---------- Mode C: edit tile ----------
  _changeTileType(t, e) {
    if (e === t.type) return;
    const s = { ...t, type: e };
    delete s.min, delete s.max, delete s.icon, delete s.severity, this._emit("tile-changed", { tile: s });
    const i = ++this._compatSeq;
    ye(this.hass, e).then((r) => {
      if (i !== this._compatSeq) return;
      this._compatible = r.entities;
      const n = this.page.tiles.find((o) => o.id === t.id);
      if (!n || n.type !== e) return;
      const a = n.entity_id ? r.entities.find((o) => o.entity_id === n.entity_id) : void 0;
      if (n.entity_id && !a) {
        const o = { ...n };
        delete o.entity_id, this._emit("tile-changed", { tile: o });
      } else a && e === "gauge" && n.min === void 0 && n.max === void 0 && this._emit("tile-changed", { tile: { ...n, ...be(a) } });
    });
  }
  _onEditEntityPicked(t, e) {
    const s = e.detail.entity, i = { ...t, entity_id: s.entity_id };
    t.type === "gauge" && t.min === void 0 && t.max === void 0 && Object.assign(i, be(s)), this._emit("tile-changed", { tile: i });
  }
  _changeRange(t, e, s) {
    const i = s.target, r = Number(i.value), n = () => i.value = String(t[e] ?? (e === "min" ? 0 : 100));
    if (!Number.isFinite(r)) {
      n();
      return;
    }
    const a = e === "min" ? r : t.min ?? 0, o = e === "max" ? r : t.max ?? 100;
    if (o <= a) {
      this._rangeError = "Max must be greater than min", n();
      return;
    }
    this._rangeError = "", this._emit("tile-changed", { tile: { ...t, min: a, max: o } });
  }
  _changeSeverity(t, e, s) {
    var o;
    const i = s.target, r = i.value.trim(), n = { ...t.severity ?? {} };
    if (r === "")
      delete n[e];
    else {
      const l = Number(r);
      if (!Number.isFinite(l)) {
        const d = (o = t.severity) == null ? void 0 : o[e];
        i.value = d === void 0 ? "" : String(d);
        return;
      }
      n[e] = l;
    }
    const a = { ...t };
    n.green === void 0 && n.yellow === void 0 && n.red === void 0 ? delete a.severity : a.severity = n, this._emit("tile-changed", { tile: a });
  }
  _changeSpan(t, e, s) {
    const i = (t.rs ?? 1) + (e === "rs" ? s : 0), r = (t.cs ?? 1) + (e === "cs" ? s : 0);
    if (i < 1 || r < 1) return;
    const n = H(this.page.tiles, t.id);
    L(t.row, t.col, i, r, this.page.rows, this.page.columns, n) && this._emit("tile-changed", { tile: { ...t, rs: i, cs: r } });
  }
  _spanStepper(t, e, s, i) {
    const r = t[e] ?? 1, n = L(
      t.row,
      t.col,
      e === "rs" ? r + 1 : t.rs ?? 1,
      e === "cs" ? r + 1 : t.cs ?? 1,
      this.page.rows,
      this.page.columns,
      i
    );
    return c`
      <label class="field">
        <span>${s}</span>
        <div class="stepper">
          <button ?disabled=${r <= 1} @click=${() => this._changeSpan(t, e, -1)}>−</button>
          <span class="stepper-value">${r}</span>
          <button
            ?disabled=${!n}
            title=${n ? "" : "No room to grow — blocked by the grid edge or another tile"}
            @click=${() => this._changeSpan(t, e, 1)}
          >
            +
          </button>
        </div>
      </label>
    `;
  }
  _renderTileEditor(t) {
    const e = H(this.page.tiles, t.id), s = !t.entity_id || this._compatible === null ? !0 : this._compatible.some((i) => i.entity_id === t.entity_id);
    return c`
      <h3>Tile</h3>
      <label class="field">
        <span>Type</span>
        ${this._renderTypeButtons(t.type, (i) => this._changeTileType(t, i))}
      </label>
      ${t.type !== "clock" ? c`
        <label class="field">
          <span>Entity</span>
          <dash480-entity-select
            .hass=${this.hass}
            .tileType=${t.type}
            .value=${t.entity_id}
            .warning=${s ? void 0 : t.type === "gauge" ? "This entity isn't currently numeric — the gauge may not render." : "This entity isn't compatible with this tile type."}
            @entity-selected=${(i) => this._onEditEntityPicked(t, i)}
          >
          </dash480-entity-select>
        </label>
        ${t.entity_id ? h : c`<div class="error">No entity selected — this tile won't show on the device.</div>`}
        ` : h}      ${t.type === "gauge" ? c`
            <div class="row2">
              <label class="field">
                <span>Min</span>
                <input
                  type="number"
                  .value=${String(t.min ?? 0)}
                  @change=${(i) => this._changeRange(t, "min", i)}
                />
              </label>
              <label class="field">
                <span>Max</span>
                <input
                  type="number"
                  .value=${String(t.max ?? 100)}
                  @change=${(i) => this._changeRange(t, "max", i)}
                />
              </label>
            </div>
            ${this._rangeError ? c`<div class="error">${this._rangeError}</div>` : h}
            <div class="severity">
              <span class="severity-title">Severity bands</span>
              ${["green", "yellow", "red"].map(
      (i) => {
        var r;
        return c`
                  <label class="field">
                    <span><i class="swatch ${i}"></i>${i[0].toUpperCase()}${i.slice(1)} from</span>
                    <input
                      type="number"
                      step="any"
                      .value=${((r = t.severity) == null ? void 0 : r[i]) === void 0 ? "" : String(t.severity[i])}
                      @change=${(n) => this._changeSeverity(t, i, n)}
                    />
                  </label>
                `;
      }
    )}
              <div class="hint">
                Each color runs from its value up to the next, around the gauge. Leave a field blank to skip
                it. Low-to-high (waste drawer) and high-to-low (salt level) both work. Clear all three for a
                single-color arc.
              </div>
            </div>
          ` : h}
      ${t.type === "entity" ? c`
            <label class="field">
              <span>Icon</span>
              <select
                @change=${(i) => {
      const r = i.target.value, n = { ...t };
      r ? n.icon = r : delete n.icon, this._emit("tile-changed", { tile: n });
    }}
              >
                <option value="" ?selected=${!t.icon}>Automatic</option>
                ${this._icons.map(
      (i) => c`
                    <option value=${i.code} ?selected=${t.icon === i.code}>${us(i.label)}</option>
                  `
    )}
              </select>
            </label>
          ` : h}
      <div class="row2">
        ${this._spanStepper(t, "rs", "Height (rows)", e)}
        ${this._spanStepper(t, "cs", "Width (columns)", e)}
      </div>
      <div class="meta">Row ${t.row + 1}, column ${t.col + 1} — drag the tile to move it.</div>
      <button class="remove" @click=${() => this._emit("tile-removed", { tileId: t.id })}>Remove tile</button>
    `;
  }
  render() {
    if (!this.page) return h;
    let t;
    if (this.selection.kind === "tile") {
      const e = this._selectedTile();
      t = e ? this._renderTileEditor(e) : this._renderPageSettings();
    } else this.selection.kind === "cell" ? t = this._renderAddForm() : t = this._renderPageSettings();
    return c`<div class="panel">${t}</div>`;
  }
};
y.styles = q`
    :host {
      display: block;
    }
    .panel {
      background: var(--card-background-color, #1e1e1e);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 200px;
    }
    h3 {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .field > span {
      font-size: 12px;
      opacity: 0.7;
    }
    input,
    select {
      padding: 8px 10px;
      font-size: 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
    }
    select option {
      background: var(--card-background-color, #1e1e1e);
    }
    .row2 {
      display: flex;
      gap: 12px;
    }
    .segmented {
      display: flex;
      border: 1px solid #555;
      border-radius: 6px;
      overflow: hidden;
    }
    .segmented button {
      flex: 1;
      padding: 8px 0;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 13px;
    }
    .segmented button + button {
      border-left: 1px solid #555;
    }
    .segmented button.active {
      background: var(--primary-color, #38bdf8);
      color: #0b1220;
      font-weight: 600;
    }
    .stepper {
      display: flex;
      align-items: center;
      gap: 4px;
      border: 1px solid #555;
      border-radius: 6px;
      overflow: hidden;
    }
    .stepper button {
      width: 34px;
      padding: 8px 0;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 16px;
    }
    .stepper button:disabled {
      opacity: 0.3;
      cursor: default;
    }
    .stepper-value {
      flex: 1;
      text-align: center;
      font-size: 14px;
    }
    .meta {
      font-size: 12px;
      opacity: 0.6;
    }
    .hint {
      font-size: 12px;
      opacity: 0.6;
      line-height: 1.4;
    }
    .error {
      font-size: 12px;
      color: #f87171;
      line-height: 1.4;
    }
    .severity {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .severity-title {
      font-size: 12px;
      opacity: 0.7;
    }
    .swatch {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-right: 6px;
    }
    .swatch.green {
      background: #43a047;
    }
    .swatch.yellow {
      background: #ffa600;
    }
    .swatch.red {
      background: #db4437;
    }
    .remove {
      margin-top: 4px;
      padding: 10px;
      border-radius: 6px;
      border: 1px solid #7f1d1d;
      background: transparent;
      color: #f87171;
      cursor: pointer;
      font-size: 13px;
    }
    .remove:hover {
      background: rgba(248, 113, 113, 0.1);
    }
  `;
k([
  f({ attribute: !1 })
], y.prototype, "hass", 2);
k([
  f({ attribute: !1 })
], y.prototype, "page", 2);
k([
  f({ attribute: !1 })
], y.prototype, "selection", 2);
k([
  u()
], y.prototype, "_addType", 2);
k([
  u()
], y.prototype, "_icons", 2);
k([
  u()
], y.prototype, "_compatible", 2);
k([
  u()
], y.prototype, "_shrinkError", 2);
k([
  u()
], y.prototype, "_rangeError", 2);
k([
  u()
], y.prototype, "_addError", 2);
y = k([
  B("dash480-inspector")
], y);
var _s = Object.defineProperty, gs = Object.getOwnPropertyDescriptor, A = (t, e, s, i) => {
  for (var r = i > 1 ? void 0 : i ? gs(e, s) : e, n = t.length - 1, a; n >= 0; n--)
    (a = t[n]) && (r = (i ? a(e, s, r) : a(r)) || r);
  return i && r && _s(e, s, r), r;
};
class fs {
  constructor(e, s) {
    this._save = e, this._onStatus = s, this._pending = null, this._inFlight = null, this._retried = !1;
  }
  schedule(e) {
    this._pending = e, this._retried = !1, clearTimeout(this._timer), this._timer = window.setTimeout(() => this._run(), 800);
  }
  // Save any pending draft now. Returns true when everything is persisted;
  // false when the save failed — callers must NOT act on the store (publish,
  // area-append) in that case, since it doesn't reflect the draft.
  async flush() {
    for (clearTimeout(this._timer); this._inFlight; ) await this._inFlight;
    return this._pending && await this._run(), this._pending === null;
  }
  // Drop any pending draft — for when the draft is about to be replaced
  // wholesale (area-append reload), so a scheduled retry can't resurrect
  // the superseded page and overwrite the reloaded one.
  discard() {
    clearTimeout(this._timer), this._pending = null;
  }
  async _run() {
    if (this._inFlight || !this._pending) return;
    const e = this._pending;
    this._pending = null, this._onStatus("saving");
    const s = Promise.resolve().then(() => this._save(e));
    this._inFlight = s.then(
      () => {
      },
      () => {
      }
    );
    let i = !1;
    try {
      await s, i = !0;
    } catch {
      this._pending === null && (this._pending = e);
    }
    if (this._inFlight = null, i) {
      if (this._pending) return this._run();
      this._onStatus("saved");
      return;
    }
    this._retried ? this._onStatus("error") : (this._retried = !0, this._timer = window.setTimeout(() => this._run(), 2e3));
  }
}
let b = class extends E {
  constructor() {
    super(...arguments), this._selection = { kind: "none" }, this._previewTiles = [], this._saveState = "idle", this._publishDirty = !1, this._publishing = !1, this._status = "", this._saver = new fs(
      (t) => Wt(this.hass, t.id, {
        title: t.title,
        columns: t.columns,
        rows: t.rows,
        tiles: t.tiles
      }),
      (t) => {
        this._saveState = t, t === "saved" && setTimeout(() => {
          this._saveState === "saved" && (this._saveState = "idle");
        }, 2e3);
      }
    ), this._previewSeq = 0;
  }
  connectedCallback() {
    super.connectedCallback(), this._draft = { ...this.initialPage, tiles: [...this.initialPage.tiles] }, this._refreshPreview();
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._saver.flush();
  }
  async _refreshPreview() {
    const t = ++this._previewSeq, { tiles: e } = await Xt(this.hass, this._draft);
    t === this._previewSeq && (this._previewTiles = e);
  }
  _applyDraft(t, e = !0) {
    this._draft = t, this._publishDirty = !0, e && this._refreshPreview(), this._saver.schedule(t);
  }
  // ---------- events from canvas ----------
  _onCellSelected(t) {
    this._selection = { kind: "cell", ...t.detail };
  }
  _onTileSelected(t) {
    this._selection = { kind: "tile", tileId: t.detail.tileId };
  }
  _onSelectionCleared() {
    this._selection = { kind: "none" };
  }
  _onTileMoved(t) {
    const { tileId: e, row: s, col: i } = t.detail;
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.map((r) => r.id === e ? { ...r, row: s, col: i } : r)
    });
  }
  _onTileResized(t) {
    const { tileId: e, rs: s, cs: i } = t.detail;
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.map((r) => r.id === e ? { ...r, rs: s, cs: i } : r)
    });
  }
  // ---------- events from inspector ----------
  _onTileAdded(t) {
    const e = t.detail.tile;
    this._applyDraft({ ...this._draft, tiles: [...this._draft.tiles, e] }), this._selection = { kind: "tile", tileId: e.id };
  }
  _onTileChanged(t) {
    const e = t.detail.tile;
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.map((s) => s.id === e.id ? e : s)
    });
  }
  _onTileRemoved(t) {
    this._applyDraft({
      ...this._draft,
      tiles: this._draft.tiles.filter((e) => e.id !== t.detail.tileId)
    }), this._selection = { kind: "none" };
  }
  _onPageChanged(t) {
    const e = t.detail.rows !== void 0 || t.detail.columns !== void 0;
    this._applyDraft({ ...this._draft, ...t.detail }, e);
  }
  // ---------- toolbar ----------
  async _back() {
    !await this._saver.flush() && !window.confirm("Your latest changes couldn't be saved. Leave anyway and lose them?") || this.dispatchEvent(new CustomEvent("editor-closed"));
  }
  _flash(t, e = 3e3) {
    this._status = t, setTimeout(() => {
      this._status === t && (this._status = "");
    }, e);
  }
  async _publish() {
    this._publishing = !0;
    try {
      if (!await this._saver.flush()) {
        this._flash("Not published — saving failed. Retry the save first.");
        return;
      }
      const e = this._previewSeq;
      await Yt(this.hass, this.panelId), e === this._previewSeq && (this._publishDirty = !1), this._flash("Published", 2e3);
    } catch {
      this._flash("Publish failed — check that the panel is loaded.");
    } finally {
      this._publishing = !1;
    }
  }
  // Called by dash480-panel before an area-append: the backend appends to
  // the *saved* page, so pending edits must land first. Returns false when
  // they couldn't be saved — the append must be aborted.
  async prepareForAreaAppend() {
    return this._saver.flush();
  }
  async reloadAfterAreaAppend() {
    this._saver.discard();
    const { pages: t } = await nt(this.hass, this.panelId), e = t.find((s) => s.id === this._draft.id);
    e && (this._draft = e, this._publishDirty = !0, this._selection = { kind: "none" }, await this._refreshPreview());
  }
  _saveLabel() {
    switch (this._saveState) {
      case "saving":
        return "Saving…";
      case "saved":
        return "Saved";
      case "error":
        return "Save failed";
      default:
        return "";
    }
  }
  render() {
    return this._draft ? c`
      <div class="toolbar">
        <button class="back" @click=${this._back}>‹ Back</button>
        <span class="page-title">${this._draft.title}</span>
        <span class="save-state ${this._saveState}">${this._saveLabel()}</span>
        ${this._saveState === "error" ? c`<button @click=${() => this._saver.flush()}>Retry</button>` : h}
        <button @click=${() => this.dispatchEvent(new CustomEvent("area-append-requested"))}>
          + Add Area Entities
        </button>
        <button class="publish ${this._publishDirty ? "dirty" : ""}" ?disabled=${this._publishing} @click=${this._publish}>
          ${this._publishing ? "Publishing…" : this._publishDirty ? "● Publish to device" : "Publish to device"}
        </button>
        <span class="status">${this._status}</span>
      </div>
      <div class="body">
        <dash480-preview-canvas
          style="flex: 0 0 ${xe}px;"
          .page=${this._draft}
          .previewTiles=${this._previewTiles}
          .selection=${this._selection}
          @cell-selected=${this._onCellSelected}
          @tile-selected=${this._onTileSelected}
          @selection-cleared=${this._onSelectionCleared}
          @tile-moved=${this._onTileMoved}
          @tile-resized=${this._onTileResized}
        ></dash480-preview-canvas>
        <dash480-inspector
          class="inspector"
          .hass=${this.hass}
          .page=${this._draft}
          .selection=${this._selection}
          @tile-added=${this._onTileAdded}
          @tile-changed=${this._onTileChanged}
          @tile-removed=${this._onTileRemoved}
          @page-changed=${this._onPageChanged}
        ></dash480-inspector>
      </div>
    ` : h;
  }
};
b.styles = q`
    :host {
      display: block;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .toolbar button {
      padding: 8px 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 13px;
    }
    .toolbar button:hover {
      border-color: #888;
    }
    .page-title {
      font-weight: bold;
      font-size: 16px;
    }
    .save-state {
      font-size: 12px;
      opacity: 0.6;
      min-width: 60px;
    }
    .save-state.error {
      color: #f87171;
      opacity: 1;
    }
    .publish.dirty {
      border-color: var(--primary-color, #38bdf8);
      color: var(--primary-color, #38bdf8);
      font-weight: 600;
    }
    .publish:disabled {
      opacity: 0.6;
      cursor: default;
    }
    .status {
      font-size: 12px;
      opacity: 0.7;
    }
    .body {
      display: flex;
      gap: 16px;
      align-items: flex-start;
      flex-wrap: wrap;
    }
    .inspector {
      flex: 1;
      min-width: 280px;
      max-width: 400px;
    }
  `;
A([
  f({ attribute: !1 })
], b.prototype, "hass", 2);
A([
  f({ attribute: !1 })
], b.prototype, "panelId", 2);
A([
  f({ attribute: !1 })
], b.prototype, "initialPage", 2);
A([
  u()
], b.prototype, "_draft", 2);
A([
  u()
], b.prototype, "_selection", 2);
A([
  u()
], b.prototype, "_previewTiles", 2);
A([
  u()
], b.prototype, "_saveState", 2);
A([
  u()
], b.prototype, "_publishDirty", 2);
A([
  u()
], b.prototype, "_publishing", 2);
A([
  u()
], b.prototype, "_status", 2);
b = A([
  B("dash480-page-editor")
], b);
var vs = Object.defineProperty, $s = Object.getOwnPropertyDescriptor, he = (t, e, s, i) => {
  for (var r = i > 1 ? void 0 : i ? $s(e, s) : e, n = t.length - 1, a; n >= 0; n--)
    (a = t[n]) && (r = (i ? a(e, s, r) : a(r)) || r);
  return i && r && vs(e, s, r), r;
};
let F = class extends E {
  constructor() {
    super(...arguments), this._areas = [], this._search = "";
  }
  connectedCallback() {
    super.connectedCallback(), Jt(this.hass).then((t) => {
      this._areas = t.areas;
    });
  }
  _filtered() {
    const t = this._search.trim().toLowerCase();
    return t ? this._areas.filter((e) => e.name.toLowerCase().includes(t)) : this._areas;
  }
  _pick(t) {
    this.dispatchEvent(new CustomEvent("area-picked", { detail: { area_id: t } }));
  }
  _cancel() {
    this.dispatchEvent(new CustomEvent("picker-closed"));
  }
  render() {
    const t = this._filtered();
    return c`
      <div class="backdrop" @click=${this._cancel}>
        <div class="dialog" @click=${(e) => e.stopPropagation()}>
          <input
            class="search"
            placeholder="Search areas…"
            .value=${this._search}
            @input=${(e) => this._search = e.target.value}
          />
          <div class="list">
            ${t.length === 0 ? c`<div class="empty">No matching areas</div>` : t.map(
      (e) => c`
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
F.styles = q`
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
he([
  f({ attribute: !1 })
], F.prototype, "hass", 2);
he([
  u()
], F.prototype, "_areas", 2);
he([
  u()
], F.prototype, "_search", 2);
F = he([
  B("dash480-area-picker")
], F);
var bs = Object.defineProperty, ys = Object.getOwnPropertyDescriptor, m = (t, e, s, i) => {
  for (var r = i > 1 ? void 0 : i ? ys(e, s) : e, n = t.length - 1, a; n >= 0; n--)
    (a = t[n]) && (r = (i ? a(e, s, r) : a(r)) || r);
  return i && r && bs(e, s, r), r;
};
let v = class extends E {
  constructor() {
    super(...arguments), this.narrow = !1, this._view = "list", this._panels = [], this._panelId = null, this._pages = [], this._reservedOrders = [], this._editingPage = null, this._newPageTitle = "", this._areaPickerMode = null, this._status = "", this._editorRef = jt();
  }
  connectedCallback() {
    super.connectedCallback(), this._loadPanels();
  }
  async _loadPanels() {
    const { panels: t } = await qt(this.hass);
    this._panels = t, t.length && !this._panelId && (this._panelId = t[0].entry_id, await this._loadPages());
  }
  async _loadPages() {
    if (!this._panelId) return;
    const { pages: t, reserved_legacy_orders: e } = await nt(this.hass, this._panelId);
    this._pages = t, this._reservedOrders = e;
  }
  async _onPanelChange(t) {
    this._panelId = t.target.value, await this._loadPages();
  }
  async _createPage() {
    if (!this._panelId || !this._newPageTitle.trim()) return;
    const { page: t } = await Bt(this.hass, this._panelId, this._newPageTitle.trim(), 3, 2);
    this._newPageTitle = "", await this._loadPages(), this._openEditor(t);
  }
  _openEditor(t) {
    this._editingPage = t, this._view = "editor";
  }
  _onEditorClosed() {
    this._view = "list", this._editingPage = null, this._loadPages();
  }
  async _deletePage(t) {
    window.confirm(`Delete page "${t.title}"? This can't be undone.`) && (await Vt(this.hass, t.id), await this._loadPages());
  }
  _openAreaPicker(t) {
    this._areaPickerMode = t;
  }
  async _onAreaPicked(t) {
    var a;
    const e = this._areaPickerMode;
    if (this._areaPickerMode = null, !e || !this._panelId) return;
    const s = this._editorRef.value, i = e === "append" ? (a = this._editingPage) == null ? void 0 : a.id : void 0;
    if (e === "append") {
      if (!i || !s) return;
      if (!await s.prepareForAreaAppend()) {
        this._status = "Couldn't save your pending edits — area append cancelled.", setTimeout(() => this._status = "", 4e3);
        return;
      }
    }
    const r = await Qt(this.hass, this._panelId, t.detail.area_id, e, i), n = r.skipped_entity_ids.length + r.skipped_incompatible_count;
    this._status = `Placed ${r.placed_count} entities${n ? `, ${n} skipped` : ""}`, setTimeout(() => this._status = "", 4e3), e === "append" && s ? await s.reloadAfterAreaAppend() : await this._loadPages();
  }
  render() {
    return this.hass ? c`
      <div class="wrap">
        ${this._view === "list" ? this._renderList() : this._renderEditor()}
      </div>
      ${this._areaPickerMode ? c`
            <dash480-area-picker
              .hass=${this.hass}
              @area-picked=${this._onAreaPicked}
              @picker-closed=${() => this._areaPickerMode = null}
            ></dash480-area-picker>
          ` : h}
    ` : h;
  }
  _renderList() {
    return c`
      <h1>Dash480</h1>
      ${this._panels.length > 1 ? c`
            <select @change=${this._onPanelChange}>
              ${this._panels.map(
      (t) => c`<option value=${t.entry_id} ?selected=${t.entry_id === this._panelId}>
                    ${t.title}
                  </option>`
    )}
            </select>
          ` : h}
      ${this._panels.length === 0 ? c`<p>No Dash480 panels configured yet. Add one from Settings &gt; Devices &amp; Services.</p>` : c`
            <div class="pages">
              ${this._reservedOrders.map(
      (t) => c`<div class="page-card reserved">Page ${t} — legacy (edit via Configure)</div>`
    )}
              ${this._pages.map(
      (t) => c`
                  <div class="page-card">
                    <div class="title" @click=${() => this._openEditor(t)}>
                      Page ${t.page_order}: ${t.title} (${t.tiles.length} tiles)
                    </div>
                    <button @click=${() => this._deletePage(t)}>Delete</button>
                  </div>
                `
    )}
            </div>
            <div class="new-page">
              <input
                placeholder="New page title"
                .value=${this._newPageTitle}
                @input=${(t) => this._newPageTitle = t.target.value}
                @keydown=${(t) => t.key === "Enter" && this._createPage()}
              />
              <button @click=${this._createPage}>+ New Page</button>
              <button @click=${() => this._openAreaPicker("new_page")}>+ Generate Page from Area</button>
            </div>
            <span class="status">${this._status}</span>
          `}
    `;
  }
  _renderEditor() {
    return c`
      <dash480-page-editor
        ${Ft(this._editorRef)}
        .hass=${this.hass}
        .panelId=${this._panelId}
        .initialPage=${this._editingPage}
        @editor-closed=${this._onEditorClosed}
        @area-append-requested=${() => this._openAreaPicker("append")}
      ></dash480-page-editor>
      <span class="status">${this._status}</span>
    `;
  }
};
v.styles = q`
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
      flex: 1;
    }
    .new-page {
      display: flex;
      gap: 8px;
    }
    .new-page input {
      padding: 8px 10px;
      font-size: 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
    }
    button {
      padding: 8px 14px;
      border-radius: 6px;
      border: 1px solid #555;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 13px;
    }
    button:hover {
      border-color: #888;
    }
    .status {
      opacity: 0.7;
      font-size: 12px;
    }
  `;
m([
  f({ attribute: !1 })
], v.prototype, "hass", 2);
m([
  f({ type: Boolean })
], v.prototype, "narrow", 2);
m([
  u()
], v.prototype, "_view", 2);
m([
  u()
], v.prototype, "_panels", 2);
m([
  u()
], v.prototype, "_panelId", 2);
m([
  u()
], v.prototype, "_pages", 2);
m([
  u()
], v.prototype, "_reservedOrders", 2);
m([
  u()
], v.prototype, "_editingPage", 2);
m([
  u()
], v.prototype, "_newPageTitle", 2);
m([
  u()
], v.prototype, "_areaPickerMode", 2);
m([
  u()
], v.prototype, "_status", 2);
v = m([
  B("dash480-panel")
], v);
export {
  v as Dash480Panel
};
