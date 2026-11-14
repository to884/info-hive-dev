/*!
THIRD-PARTY NOTICES

このスキルの CSS、JS、トークンの値、設計書は、次のソフトウェアから値と規則を写して作った非公式の再現である。
Fluent、Microsoft、Segoe は Microsoft Corporation の商標である。このスキルは Microsoft の製品ではなく、Microsoft が推奨するものでもない。

------------------------------------------------------------------------
1. Fluent UI（microsoft/fluentui、commit f9720c35ba893c9630f4c0389d07dc6d6fd6068d）
   対象: トークンの値（@fluentui/tokens）、コンポーネントのスタイルの規則（@fluentui/react-components、@fluentui/web-components）、
         scripts/brand_ramp.py と scripts/_hue_map.py（テーマデザイナー packages/react-components/theme-designer の色の計算を写したもの。
         テーマデザイナーの色の変換は CSSWG の CSS Color 4 のサンプルコード、曲線は three.js に由来すると、元のコードに記されている）
   https://github.com/microsoft/fluentui
------------------------------------------------------------------------

MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE

NOTE: Usage of the fonts and icons referenced in Fluent UI React is subject to the terms listed at https://aka.ms/fluentui-assets-license

------------------------------------------------------------------------
2. Fluent UI System Icons（microsoft/fluentui-system-icons、@fluentui/svg-icons 1.1.345）
   対象: 設計書と参照の原稿の例に埋め込んだ SVG のアイコンの形
   https://github.com/microsoft/fluentui-system-icons
------------------------------------------------------------------------

MIT License

Copyright (c) 2020 Microsoft Corporation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------------------------------------------------
3. three.js（mrdoob/three.js、r133 の当時の版）
   対象: scripts/brand_ramp.py の 2 次ベジェ曲線の計算。テーマデザイナーの colors/geometry.ts が three.js から写したと記している
   https://github.com/mrdoob/three.js
------------------------------------------------------------------------

The MIT License

Copyright © 2010-2021 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

------------------------------------------------------------------------
4. css.land の lch.js と multiply-matrices.js（Lea Verou）
   対象: scripts/brand_ramp.py の色域への収め方（snap_into_gamut）と、行列とベクトルの積。
         テーマデザイナーの colors/csswg.ts が、LeaVerou/css.land の lch/lch.js と、
         「@author Lea Verou 2020 MIT License」と記した multiply-matrices.js から写したと記している
   https://github.com/LeaVerou/css.land
------------------------------------------------------------------------

MIT License

Copyright (c) 2021 Lea Verou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------------------------------------------------
5. CSS Color Module Level 4 のサンプルコード（W3C の CSS Working Group）
   対象: scripts/brand_ramp.py の色空間の変換（sRGB、XYZ、D50 と D65、Lab、LCH）。
         テーマデザイナーの colors/csswg.ts が https://drafts.csswg.org/css-color-4/conversions.js から写したと記している
------------------------------------------------------------------------

This software includes material derived from CSS Color Module Level 4, sample code for color conversions
(https://drafts.csswg.org/css-color-4/conversions.js). Copyright © 2021 World Wide Web Consortium.
https://www.w3.org/copyright/software-license-2023/

W3C Software and Document License（2023 年版）
https://www.w3.org/copyright/software-license-2023/

This work is being provided by the copyright holders under the following license.

License

By obtaining and/or copying this work, you (the licensee) agree that you have read, understood, and will comply with the following terms and conditions.

Permission to copy, modify, and distribute this work, with or without modification, for any purpose and without fee or royalty is hereby granted, provided that you include the following on ALL copies of the work or portions thereof, including modifications:

- The full text of this NOTICE in a location viewable to users of the redistributed or derivative work.
- Any pre-existing intellectual property disclaimers, notices, or terms and conditions. If none exist, the W3C software and document short notice should be included.
- Notice of any changes or modifications, through a copyright statement on the new code or document such as "This software or document includes material copied from or derived from [title and URI of the W3C document]. Copyright © [$year-of-document] World Wide Web Consortium. https://www.w3.org/copyright/software-license-2023/"

Disclaimers

THIS WORK IS PROVIDED "AS IS," AND COPYRIGHT HOLDERS MAKE NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO, WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE OR DOCUMENT WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.

COPYRIGHT HOLDERS WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF ANY USE OF THE SOFTWARE OR DOCUMENT.

The name and trademarks of copyright holders may NOT be used in advertising or publicity pertaining to the work without specific, written prior permission. Title to copyright in this work will at all times remain with copyright holders.

------------------------------------------------------------------------
6. 書体について
------------------------------------------------------------------------

フォントの並び（font-family）は Segoe UI、Yu Gothic UI、Meiryo UI などの書体名を指すだけで、書体のファイルは同梱しない。
これらの書体を Web フォントとして配ったり、形式を変えたりしてはならない。
*/
// このファイルは tools/build_spec.py が components/ から生成する。手で直さない
/*!
 * Fluent 2 Web のアクション系コンポーネントの小さな振る舞い（非公式）
 * CSS だけでは表せないものに限る: disabledFocusable の操作の抑止、role="button" の Enter と Space、
 * ToggleButton の aria-pressed / aria-checked の切り替え、Toolbar の矢印キーのローヴィング、
 * popover を開くボタン（MenuButton、InfoButton）の aria-expanded と InfoButton の位置。
 * 元の振る舞いは microsoft/fluentui（MIT License、Copyright (c) Microsoft Corporation）の
 * react-aria の useARIAButtonProps、react-button の useToggleState、react-toolbar の useToolbar、
 * react-infolabel の useInfoButton による。
 * 対象は data-fui-enhance を付けた要素とその中だけ。依存なし、ES2020。
 */
(() => {
  'use strict';

  const ENHANCE = '[data-fui-enhance]';
  const CONTROL = '.fui-Button, .fui-Link, .fui-InfoButton';

  const enhanced = (el) => el instanceof Element && el.closest(ENHANCE) !== null;

  // aria-disabled="true" の部品（disabledFocusable）。フォーカスは残し、操作は止める
  // （react-aria/library/src/button/useARIAButtonProps.ts:70-74、97-101）
  const blockedControl = (target) => {
    if (!(target instanceof Element)) return null;
    const control = target.closest(CONTROL);
    if (!control || !enhanced(control)) return null;
    return control.getAttribute('aria-disabled') === 'true' ? control : null;
  };

  // <a> や <span> を role="button" で使うときの Enter（keydown）と Space（keyup）（useARIAButtonProps.ts:81-85、103-106）
  //   対象は v9 で useARIAButtonProps を使う部品（CONTROL）に限る。ほかの部品の role="button"
  //   （Combobox の展開アイコンなど）は、その部品が自分でキーを扱うので、ここで扱うと二重に動く
  const isPseudoButton = (el) =>
    el instanceof Element && enhanced(el) && el.matches('[role="button"]') && el.matches(CONTROL) &&
    el.tagName !== 'BUTTON' && el.tagName !== 'INPUT';

  const init = () => {
    document.addEventListener('click', (ev) => {
      if (blockedControl(ev.target)) {
        ev.preventDefault();
        ev.stopImmediatePropagation();
      }
    }, true);

    document.addEventListener('keydown', (ev) => {
      if (ev.key !== 'Enter' && ev.key !== ' ') return;
      if (blockedControl(ev.target)) {
        ev.preventDefault();
        ev.stopImmediatePropagation();
        return;
      }
      if (isPseudoButton(ev.target)) {
        ev.preventDefault();
        if (ev.key === 'Enter') ev.target.click();
      }
    }, true);

    document.addEventListener('keyup', (ev) => {
      if (ev.key === ' ' && isPseudoButton(ev.target) && !blockedControl(ev.target)) {
        ev.preventDefault();
        ev.target.click();
      }
    }, true);

    // ToggleButton（useToggleState.ts）。role が radio なら、同じ data-name の仲間を外す（useToolbar.ts の handleRadio）
    document.addEventListener('click', (ev) => {
      if (!(ev.target instanceof Element)) return;
      const button = ev.target.closest('.fui-ToggleButton');
      if (!button || !enhanced(button) || button.matches(':disabled')) return;
      const role = button.getAttribute('role');
      if (role === 'radio') {
        const scope = button.closest('.fui-Toolbar, [role="radiogroup"]') || document;
        const name = button.getAttribute('data-name');
        scope.querySelectorAll('.fui-ToggleButton[role="radio"]').forEach((other) => {
          if (other.getAttribute('data-name') === name) other.setAttribute('aria-checked', String(other === button));
        });
      } else if (role === 'checkbox' || role === 'menuitemcheckbox') {
        button.setAttribute('aria-checked', String(button.getAttribute('aria-checked') !== 'true'));
      } else {
        button.setAttribute('aria-pressed', String(button.getAttribute('aria-pressed') !== 'true'));
      }
    });

    document.querySelectorAll(`.fui-Toolbar${ENHANCE}`).forEach(setupToolbar);
    document.querySelectorAll(`${ENHANCE}[popovertarget], ${ENHANCE} [popovertarget]`).forEach(setupPopoverInvoker);
  };

  // Toolbar: 矢印キーで項目を移り、端で反対側に回る（axis: 'both'、circular: true。react-toolbar/library/src/components/Toolbar/useToolbar.ts:146-149）。
  // Tab は Toolbar の外へ出て、戻ると最後にフォーカスした項目に入る（memorizeCurrent の既定）。
  const ITEM = 'button, a[href], input, select, textarea, [role="button"], [role="radio"], [role="checkbox"]';
  const setupToolbar = (toolbar) => {
    const items = () =>
      Array.from(toolbar.querySelectorAll(ITEM)).filter((el) => !el.matches(':disabled') && el.getClientRects().length > 0);
    const activate = (target) => {
      items().forEach((el) => el.setAttribute('tabindex', el === target ? '0' : '-1'));
    };
    const list = items();
    const start = list.find((el) => el.getAttribute('tabindex') === '0') || list[0];
    if (start) activate(start);

    toolbar.addEventListener('focusin', (ev) => {
      const item = ev.target instanceof Element ? ev.target.closest(ITEM) : null;
      if (item && toolbar.contains(item)) activate(item);
    });

    toolbar.addEventListener('keydown', (ev) => {
      const all = items();
      const index = all.indexOf(document.activeElement);
      if (index < 0) return;
      const editable = document.activeElement.matches('input, select, textarea');
      const rtl = getComputedStyle(toolbar).direction === 'rtl';
      let next = null;
      switch (ev.key) {
        case 'ArrowRight':
          if (editable) return;
          next = rtl ? index - 1 : index + 1;
          break;
        case 'ArrowLeft':
          if (editable) return;
          next = rtl ? index + 1 : index - 1;
          break;
        case 'ArrowDown':
          next = index + 1;
          break;
        case 'ArrowUp':
          next = index - 1;
          break;
        case 'Home':
          if (editable) return;
          next = 0;
          break;
        case 'End':
          if (editable) return;
          next = all.length - 1;
          break;
        default:
          return;
      }
      ev.preventDefault();
      const target = all[(next + all.length) % all.length];
      activate(target);
      target.focus();
    });
  };

  // popover を開くボタン: aria-expanded を開閉に合わせる。InfoButton は上・先頭側に置き、フォーカスが外へ出たら閉じる
  // （react-infolabel/library/src/components/InfoButton/useInfoButton.tsx:24-28、95-107、InfoLabel/useInfoLabel.ts:83-85）
  const GAP = 4; // v9 の値ではない（react-positioning の offset と矢印は再現しない）
  const setupPopoverInvoker = (invoker) => {
    const surface = document.getElementById(invoker.getAttribute('popovertarget'));
    if (!surface) return;
    const isInfo = invoker.classList.contains('fui-InfoButton');
    const infoLabel = isInfo ? invoker.closest('.fui-InfoLabel') : null;

    const place = () => {
      const anchor = invoker.getBoundingClientRect();
      const rtl = getComputedStyle(invoker).direction === 'rtl';
      surface.style.margin = '0';
      surface.style.inset = 'auto';
      const height = surface.offsetHeight;
      const top = anchor.top - GAP - height >= 0 ? anchor.top - GAP - height : anchor.bottom + GAP;
      surface.style.top = `${Math.round(top)}px`;
      if (rtl) {
        surface.style.right = `${Math.round(document.documentElement.clientWidth - anchor.right)}px`;
      } else {
        surface.style.left = `${Math.round(Math.max(0, anchor.left))}px`;
      }
    };

    const onFocusOut = (ev) => {
      const next = ev.relatedTarget;
      if (next instanceof Node && (invoker.contains(next) || surface.contains(next))) return;
      if (surface.matches(':popover-open')) surface.hidePopover();
    };

    surface.addEventListener('toggle', (ev) => {
      const open = ev.newState === 'open';
      invoker.setAttribute('aria-expanded', String(open));
      if (!isInfo) return;
      if (infoLabel) {
        if (open) infoLabel.setAttribute('aria-owns', surface.id);
        else infoLabel.removeAttribute('aria-owns');
      }
      if (open) {
        place();
        window.addEventListener('scroll', place, true);
        window.addEventListener('resize', place);
        invoker.addEventListener('focusout', onFocusOut);
        surface.addEventListener('focusout', onFocusOut);
      } else {
        window.removeEventListener('scroll', place, true);
        window.removeEventListener('resize', place);
        invoker.removeEventListener('focusout', onFocusOut);
        surface.removeEventListener('focusout', onFocusOut);
      }
    });
    invoker.setAttribute('aria-expanded', String(surface.matches(':popover-open')));
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();

/*!
 * Fluent 2 Web の文字入力と選択のコンポーネントの小さな振る舞い（非公式）
 * CSS だけでは表せないものに限る: Combobox と Dropdown の開閉、選択、aria-activedescendant と
 * data-activedescendant-focusvisible、一覧の位置、SpinButton の増減、SearchBox の消去ボタン。
 * 元の振る舞いは microsoft/fluentui（MIT License、Copyright (c) Microsoft Corporation）の
 * react-combobox の useTriggerSlot と dropdownKeyActions、react-spinbutton の useSpinButton、
 * react-search の useSearchBox による。
 * 対象は data-fui-enhance を付けた要素とその中だけ。依存なし、ES2020。
 * 出典のパスは packages/react-components/ からの相対パス。
 */
(() => {
  'use strict';

  const ENHANCE = '[data-fui-enhance]';
  let uid = 0;
  const ensureId = (el, prefix) => {
    if (!el.id) {
      uid += 1;
      el.id = `${prefix}-${uid}`;
    }
    return el.id;
  };
  const scope = (selector) => {
    const found = new Set();
    document.querySelectorAll(ENHANCE).forEach((host) => {
      if (host.matches(selector)) found.add(host);
      host.querySelectorAll(selector).forEach((el) => found.add(el));
    });
    return [...found];
  };

  /* ------------------------------------------------------------------------
     Combobox と Dropdown
     キーの割り当て: react-combobox/library/src/utils/dropdownKeyActions.ts:31-90
     動作: react-combobox/library/src/utils/useTriggerSlot.ts:67-205、
           開いたときの強調: react-combobox/library/src/utils/useComboboxBaseState.ts:155-169
     一覧の位置: react-combobox/library/src/utils/useComboboxPositioning.ts:17-27（下、始端、2px、幅を合わせる）
     ------------------------------------------------------------------------ */
  const getAction = (e, open, multiselect) => {
    const { key, altKey, ctrlKey, metaKey } = e;
    if (key.length === 1 && key !== ' ' && !altKey && !ctrlKey && !metaKey) return 'Type';
    if (!open) {
      return ['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(key) ? 'Open' : 'None';
    }
    if ((key === 'ArrowUp' && altKey) || key === 'Enter' || (!multiselect && key === ' ')) return 'CloseSelect';
    if (multiselect && key === ' ') return 'Select';
    if (key === 'Escape') return 'Close';
    const nav = { ArrowDown: 'Next', ArrowUp: 'Previous', Home: 'First', End: 'Last', PageUp: 'PageUp', PageDown: 'PageDown', Tab: 'Tab' };
    return nav[key] || 'None';
  };

  const optionText = (opt) => (opt.getAttribute('data-text') ?? opt.textContent ?? '').trim();
  const isSelected = (opt) => opt.getAttribute('aria-selected') === 'true' || opt.getAttribute('aria-checked') === 'true';

  const setupPicker = (root) => {
    if (root.__fuiPicker) return;
    const isCombobox = root.classList.contains('fui-Combobox');
    const trigger = root.querySelector(isCombobox ? '.fui-Combobox__input' : '.fui-Dropdown__button');
    const listbox = root.querySelector('.fui-Listbox');
    if (!trigger || !listbox) return;
    root.__fuiPicker = true;

    const expandIcon = root.querySelector('.fui-Combobox__expandIcon');
    const clear = root.querySelector('.fui-Combobox__clearIcon, .fui-Dropdown__clearButton');
    const options = () => [...listbox.querySelectorAll('.fui-Option')];
    const multiselect = () => listbox.getAttribute('role') === 'menu' || options().some((o) => o.getAttribute('role') === 'menuitemcheckbox');
    const supportsPopover = typeof listbox.showPopover === 'function';
    if (supportsPopover && !listbox.hasAttribute('popover')) listbox.setAttribute('popover', 'manual');
    if (!supportsPopover) listbox.hidden = true;
    ensureId(listbox, 'fui-listbox');
    options().forEach((o) => ensureId(o, 'fui-option'));

    let open = false;
    let active = null;
    let keyboard = false;
    let isTyping = false; // Combobox で、最後の操作が文字の入力だったか（useInputTriggerSlot.ts:144-161）
    let typed = '';
    let typedTimer = 0;

    const place = () => {
      const r = root.getBoundingClientRect();
      const gap = 2; // mainAxis: 2（v9 の直書き）
      listbox.style.position = 'fixed';
      listbox.style.width = `${r.width}px`;
      listbox.style.maxHeight = '';
      const below = window.innerHeight - r.bottom - gap;
      const above = r.top - gap;
      const h = listbox.offsetHeight;
      // 入らなければ上へ反転する（v9 の fallbackPositions の最初の 'above' だけを再現する）
      if (h <= below || below >= above) {
        listbox.style.top = `${r.bottom + gap}px`;
        listbox.style.maxHeight = `min(80vh, ${Math.max(below, 0)}px)`;
      } else {
        listbox.style.maxHeight = `min(80vh, ${Math.max(above, 0)}px)`;
        listbox.style.top = `${r.top - gap - Math.min(h, above)}px`;
      }
      listbox.style.left = `${r.left}px`;
    };

    const setActive = (opt) => {
      if (active) {
        active.removeAttribute('data-activedescendant');
        active.removeAttribute('data-activedescendant-focusvisible');
      }
      active = opt || null;
      if (!active) {
        trigger.removeAttribute('aria-activedescendant');
        return;
      }
      active.setAttribute('data-activedescendant', '');
      if (keyboard) active.setAttribute('data-activedescendant-focusvisible', '');
      trigger.setAttribute('aria-activedescendant', active.id);
      active.scrollIntoView({ block: 'nearest' });
    };

    const show = () => {
      if (open || trigger.disabled) return;
      open = true;
      if (supportsPopover) listbox.showPopover();
      else listbox.hidden = false;
      place();
      trigger.setAttribute('aria-expanded', 'true');
      trigger.setAttribute('aria-controls', listbox.id);
      if (expandIcon) expandIcon.setAttribute('aria-expanded', 'true');
      // 単一選択で選択があれば、それを強調する。なければ最初の選択肢
      const list = options();
      const selected = !multiselect() ? list.find(isSelected) : undefined;
      setActive(selected || list[0]);
    };

    const hide = () => {
      if (!open) return;
      open = false;
      if (supportsPopover) listbox.hidePopover();
      else listbox.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      trigger.removeAttribute('aria-controls');
      if (expandIcon) expandIcon.setAttribute('aria-expanded', 'false');
      setActive(null);
    };

    // initial が真のときは、選択がなければマークアップの文字をそのまま残す
    const render = (initial = false) => {
      const texts = options().filter(isSelected).map(optionText);
      const value = texts.join(', ');
      const placeholder = trigger.getAttribute(isCombobox ? 'placeholder' : 'data-placeholder') || '';
      if (clear) clear.hidden = texts.length === 0;
      if (initial && texts.length === 0 && (isCombobox || placeholder === '')) return;
      if (isCombobox) {
        trigger.value = value;
        return;
      }
      // 選択値の文字は、button の最初の子要素（開くアイコン以外）に置く
      let holder = [...trigger.children].find((n) => !n.classList.contains('fui-Dropdown__expandIcon'));
      if (!holder) {
        holder = document.createElement('span');
        trigger.insertBefore(holder, trigger.firstChild);
      }
      holder.textContent = value || placeholder;
      trigger.toggleAttribute('data-placeholder-visible', !value && placeholder !== '');
    };

    const select = (opt) => {
      if (!opt || opt.getAttribute('aria-disabled') === 'true') return;
      if (multiselect()) {
        opt.setAttribute('aria-checked', String(!isSelected(opt)));
      } else {
        options().forEach((o) => o.setAttribute('aria-selected', String(o === opt)));
      }
      render();
      trigger.dispatchEvent(new Event('change', { bubbles: true }));
    };

    const move = (fn) => {
      const list = options();
      if (list.length === 0) return;
      const i = active ? list.indexOf(active) : -1;
      setActive(list[Math.max(0, Math.min(list.length - 1, fn(i, list.length)))]);
    };

    const findByPrefix = (prefix, from) => {
      const list = options();
      const p = prefix.toLowerCase();
      const start = Math.max(0, from);
      for (let k = 0; k < list.length; k += 1) {
        const o = list[(start + k) % list.length];
        if (optionText(o).toLowerCase().startsWith(p)) return o;
      }
      return undefined;
    };

    trigger.addEventListener('click', () => (open ? hide() : show()));
    trigger.addEventListener('blur', () => hide());
    trigger.addEventListener('keydown', (e) => {
      const action = getAction(e, open, multiselect());
      if (isCombobox) {
        if (action === 'Type') isTyping = true;
        else if ((action === 'Open' && e.key !== ' ') || ['Next', 'Previous', 'First', 'Last', 'PageUp', 'PageDown'].includes(action)) isTyping = false;
        // 入力中か一覧が閉じているときの Space は、選択の操作にせず文字として入れる（useInputTriggerSlot.ts:164-168）
        if ((isTyping || !open) && e.key === ' ') return;
      }
      if (['First', 'Last', 'Next', 'Previous', 'PageDown', 'PageUp', 'Open', 'Close', 'CloseSelect', 'Select'].includes(action)) {
        e.preventDefault();
      }
      keyboard = true;
      switch (action) {
        case 'First': move(() => 0); break;
        case 'Last': move((i, n) => n - 1); break;
        case 'Next': move((i) => (i < 0 ? 0 : i + 1)); break;
        case 'Previous': move((i) => (i < 0 ? 0 : i - 1)); break;
        case 'PageDown': move((i) => i + 10); break;
        case 'PageUp': move((i) => i - 10); break;
        case 'Open': show(); break;
        case 'Close': e.stopPropagation(); hide(); break;
        case 'CloseSelect':
          if (!multiselect() && active && active.getAttribute('aria-disabled') !== 'true') {
            select(active);
            hide();
          } else if (active) {
            select(active);
          }
          break;
        case 'Select': select(active); break;
        case 'Tab': if (!multiselect() && active) select(active); break;
        case 'Type':
          // Dropdown は打った文字で始まる選択肢へ移る（Combobox は input イベントで扱う）
          if (!isCombobox) {
            window.clearTimeout(typedTimer);
            typed += e.key;
            typedTimer = window.setTimeout(() => { typed = ''; }, 500);
            show();
            const list = options();
            const found = findByPrefix(typed, typed.length === 1 && active ? list.indexOf(active) + 1 : list.indexOf(active));
            if (found) setActive(found);
          }
          break;
        default: break;
      }
    });
    if (isCombobox) {
      trigger.addEventListener('input', () => {
        keyboard = true;
        show();
        const found = trigger.value ? findByPrefix(trigger.value, 0) : undefined;
        if (found) setActive(found);
      });
    }
    root.addEventListener('pointerdown', () => { keyboard = false; if (active) active.removeAttribute('data-activedescendant-focusvisible'); }, true);

    // 一覧を押してもフォーカスを起点に残す
    listbox.addEventListener('mousedown', (e) => e.preventDefault());
    listbox.addEventListener('click', (e) => {
      const opt = e.target instanceof Element ? e.target.closest('.fui-Option') : null;
      if (!opt || !listbox.contains(opt) || opt.getAttribute('aria-disabled') === 'true') return;
      setActive(opt);
      select(opt);
      if (!multiselect()) hide();
      trigger.focus();
    });

    if (expandIcon) {
      expandIcon.addEventListener('mousedown', (e) => e.preventDefault());
      expandIcon.addEventListener('click', () => {
        if (trigger.disabled) return;
        if (open) hide(); else show();
        trigger.focus();
      });
      expandIcon.addEventListener('keydown', (e) => {
        if (open && e.key === 'Escape') {
          e.preventDefault();
          e.stopPropagation();
          hide();
          trigger.focus();
          return;
        }
        if (!trigger.disabled && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          if (open) hide(); else show();
          trigger.focus();
        }
      });
    }
    if (clear) {
      clear.addEventListener('mousedown', (e) => e.preventDefault());
      clear.addEventListener('click', () => {
        options().forEach((o) => o.setAttribute(o.getAttribute('role') === 'menuitemcheckbox' ? 'aria-checked' : 'aria-selected', 'false'));
        render();
        trigger.focus();
      });
    }
    const reposition = () => { if (open) place(); };
    window.addEventListener('resize', reposition);
    window.addEventListener('scroll', reposition, true);
    render(true);
  };

  /* ------------------------------------------------------------------------
     SpinButton
     react-spinbutton/library/src/components/SpinButton/useSpinButton.tsx:
     間隔 39-46（最初 300ms、1000ms かけて 80ms へ線形に縮める）、増減 110-150、キー 190-238、端のボタンの無効 313-342
     値の属性: aria-valuemin、aria-valuemax（min、max）、根の data-step、data-step-page（step、stepPage。既定 1）
     ------------------------------------------------------------------------ */
  const DEFAULT_SPIN_DELAY_MS = 300;
  const MIN_SPIN_DELAY_MS = 80;
  const MAX_SPIN_TIME_MS = 1000;
  const toNumber = (v) => (v === null || v === '' || Number.isNaN(Number(v)) ? undefined : Number(v));
  const precisionOf = (n) => {
    const m = /\.([0-9]*)/.exec(String(n));
    return m ? m[1].length : 0;
  };

  const setupSpin = (root) => {
    if (root.__fuiSpin) return;
    const input = root.querySelector('.fui-SpinButton__input');
    const inc = root.querySelector('.fui-SpinButton__incrementButton');
    const dec = root.querySelector('.fui-SpinButton__decrementButton');
    if (!input || !inc || !dec) return;
    root.__fuiSpin = true;

    const min = toNumber(input.getAttribute('aria-valuemin'));
    const max = toNumber(input.getAttribute('aria-valuemax'));
    const step = toNumber(root.getAttribute('data-step')) ?? 1;
    const stepPage = toNumber(root.getAttribute('data-step-page')) ?? 1;
    const precision = Math.max(precisionOf(step), 0);
    const round = (v) => Math.round(v * 10 ** precision) / 10 ** precision;
    const clamp = (v) => {
      let n = v;
      if (min !== undefined && !(max !== undefined && min > max)) n = Math.max(n, min);
      if (max !== undefined && !(min !== undefined && min > max)) n = Math.min(n, max);
      return n;
    };

    let value = toNumber(input.value) ?? null;
    let committedText = input.value;
    let timer = 0;
    let spinDelay = DEFAULT_SPIN_DELAY_MS;
    let spinTime = 0;

    const sync = () => {
      const atMin = value !== null && min !== undefined && value === min;
      const atMax = value !== null && max !== undefined && value === max;
      const locked = input.disabled || input.readOnly;
      inc.disabled = locked || atMax;
      dec.disabled = locked || atMin;
      if (value === null) input.removeAttribute('aria-valuenow');
      else input.setAttribute('aria-valuenow', String(value));
    };
    const commit = (v) => {
      if (v !== null && !Number.isNaN(v)) value = round(v);
      input.value = value === null ? '' : String(value);
      committedText = input.value;
      sync();
      input.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const fromText = () => {
      const n = parseFloat(input.value);
      return Number.isNaN(n) ? value : n;
    };
    const stepValue = (dir, page) => {
      const size = page ? stepPage : step;
      const start = fromText();
      if (start === null) {
        commit(clamp((min === undefined ? 0 : min) + size * dir));
        return;
      }
      commit(clamp(start + size * dir));
    };
    const stopSpin = () => {
      window.clearTimeout(timer);
      spinDelay = DEFAULT_SPIN_DELAY_MS;
      spinTime = 0;
    };
    const spin = (dir) => {
      stepValue(dir, false);
      timer = window.setTimeout(() => {
        spinTime += spinDelay;
        spinDelay = DEFAULT_SPIN_DELAY_MS + (MIN_SPIN_DELAY_MS - DEFAULT_SPIN_DELAY_MS) * (spinTime / MAX_SPIN_TIME_MS);
        spin(dir);
      }, spinDelay);
    };

    [[inc, 1], [dec, -1]].forEach(([button, dir]) => {
      button.addEventListener('mousedown', (e) => {
        if (button.disabled || e.button !== 0) return;
        e.preventDefault();
        input.focus();
        stopSpin();
        spin(dir);
      });
      button.addEventListener('mouseup', stopSpin);
      button.addEventListener('mouseleave', stopSpin);
    });

    const pressed = (button) => {
      inc.classList.toggle('fui-SpinButton__button_active', button === inc);
      dec.classList.toggle('fui-SpinButton__button_active', button === dec);
    };
    input.addEventListener('keydown', (e) => {
      if (input.readOnly) return;
      let state = null;
      if (e.key === 'ArrowUp') { e.preventDefault(); stepValue(1, false); state = inc; }
      else if (e.key === 'ArrowDown') { e.preventDefault(); stepValue(-1, false); state = dec; }
      else if (e.key === 'PageUp') { e.preventDefault(); stepValue(1, true); state = inc; }
      else if (e.key === 'PageDown') { e.preventDefault(); stepValue(-1, true); state = dec; }
      else if (!e.shiftKey && e.key === 'Home' && min !== undefined) { commit(min); state = dec; }
      else if (!e.shiftKey && e.key === 'End' && max !== undefined) { commit(max); state = inc; }
      else if (e.key === 'Enter') { commit(fromText()); }
      else if (e.key === 'Escape') { input.value = committedText; }
      pressed(state);
    });
    input.addEventListener('keyup', () => pressed(null));
    input.addEventListener('blur', () => { pressed(null); if (input.value !== committedText) commit(fromText()); });
    sync();
  };

  /* ------------------------------------------------------------------------
     SearchBox の消去ボタン（react-search/library/src/components/SearchBox/useSearchBox.tsx:125-159）
     押すと値を空にして入力欄にフォーカスを戻す。無効と読み取り専用では消さない
     ------------------------------------------------------------------------ */
  const setupSearch = (root) => {
    if (root.__fuiSearch) return;
    const input = root.querySelector('.fui-SearchBox__input');
    const dismiss = root.querySelector('.fui-SearchBox__dismiss');
    if (!input || !dismiss) return;
    root.__fuiSearch = true;
    // 押した瞬間にフォーカスが外れて消去ボタンが畳まれないようにする
    dismiss.addEventListener('mousedown', (e) => e.preventDefault());
    dismiss.addEventListener('click', () => {
      if (input.disabled || input.readOnly) return;
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.focus();
    });
  };

  /* TagPickerControl の aside の幅（v9 は useTagPickerControl で測り、--fui-TagPickerControl-aside-width に入れる。
     useTagPickerControlStyles.styles.ts:19）。CSSOM で書くので CSP（style-src 'self'）の下でも効く */
  const setupTagPickerAside = (root) => {
    const aside = root.querySelector('.fui-TagPickerControl__aside');
    if (!aside || root.__fuiAside) return;
    root.__fuiAside = true;
    const write = () => root.style.setProperty('--fui-TagPickerControl-aside-width', `${aside.getBoundingClientRect().width}px`);
    write();
    if (typeof ResizeObserver === 'function') new ResizeObserver(write).observe(aside);
  };

  const init = () => {
    scope('.fui-Combobox, .fui-Dropdown').forEach(setupPicker);
    scope('.fui-SpinButton').forEach(setupSpin);
    scope('.fui-SearchBox').forEach(setupSearch);
    scope('.fui-TagPickerControl').forEach(setupTagPickerAside);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

/*!
 * Fluent 2 Web の選択の部品の小さな振る舞い（非公式）
 * CSS だけでは表せない 3 つだけを扱う。対象は data-fui-enhance を付けた要素に限る。
 * - Checkbox: 根の data-checked="mixed" を、input のネイティブの indeterminate に写す（初期値のみ）
 * - Slider: input の値の百分率と step を、根の --fui-Slider--progress と --fui-Slider--steps-percent に写す
 * - Rating: 選んだ値と hover 中の値から、各 RatingItem の data-icon-fill-width（0、0.5、1）を決める
 * 元の実装は microsoft/fluentui（MIT License、Copyright (c) Microsoft Corporation）。
 * 基準: @fluentui/react-components 9.75.2（commit f9720c35ba893c9630f4c0389d07dc6d6fd6068d）。
 */
(() => {
  'use strict';

  // Checkbox: v9 は checked === 'mixed' のとき input.indeterminate = true にする（useCheckbox.tsx の useIsomorphicLayoutEffect）
  const enhanceCheckbox = (root) => {
    const input = root.querySelector(':scope > .fui-Checkbox__input');
    if (input && root.getAttribute('data-checked') === 'mixed') {
      input.indeterminate = true;
    }
  };

  // Slider: useSliderState.tsx:19-44 と同じ計算
  const enhanceSlider = (root) => {
    const input = root.querySelector(':scope > .fui-Slider__input');
    if (!input) return;
    const sync = () => {
      const min = input.min === '' ? 0 : Number(input.min);
      const max = input.max === '' ? 100 : Number(input.max);
      const value = Math.min(Math.max(Number(input.value), min), max);
      const percent = max === min ? 0 : ((value - min) * 100) / (max - min);
      root.style.setProperty('--fui-Slider--progress', `${percent}%`);
      // step を書いたときだけ目盛りを描く（v9 は step を渡したときだけ変数を置く）
      const step = Number(input.getAttribute('step'));
      if (input.hasAttribute('step') && step > 0 && max > min) {
        root.style.setProperty('--fui-Slider--steps-percent', `${(step * 100) / (max - min)}%`);
      } else {
        root.style.removeProperty('--fui-Slider--steps-percent');
      }
    };
    input.addEventListener('input', sync);
    input.addEventListener('change', sync);
    sync();
  };

  // Rating: useRatingItem.tsx:49-62 と useRating.tsx の onChange、onMouseOver、onMouseLeave と同じ考え方
  const enhanceRating = (root) => {
    const items = Array.from(root.querySelectorAll(':scope > .fui-RatingItem'));
    const isRatingInput = (el) => el instanceof HTMLInputElement && el.type === 'radio' && root.contains(el);
    let hovered;
    const render = () => {
      const checked = root.querySelector('input[type="radio"]:checked');
      const value = checked ? Number(checked.value) : 0;
      const ratingValue = Math.round(value * 2) / 2; // 0.5 単位に丸める
      const displayed = hovered ?? ratingValue;
      items.forEach((item, index) => {
        const itemValue = index + 1;
        let fill = 0;
        if (displayed >= itemValue) fill = 1;
        else if (displayed >= itemValue - 0.5) fill = 0.5;
        item.setAttribute('data-icon-fill-width', String(fill));
      });
    };
    root.addEventListener('change', (ev) => {
      if (isRatingInput(ev.target)) render();
    });
    root.addEventListener('mouseover', (ev) => {
      if (isRatingInput(ev.target)) {
        const v = parseFloat(ev.target.value);
        if (!Number.isNaN(v)) {
          hovered = v;
          render();
        }
      }
    });
    root.addEventListener('mouseleave', () => {
      hovered = undefined;
      render();
    });
    render();
  };

  const init = () => {
    document.querySelectorAll('.fui-Checkbox[data-fui-enhance]').forEach(enhanceCheckbox);
    document.querySelectorAll('.fui-Slider[data-fui-enhance]').forEach(enhanceSlider);
    document.querySelectorAll('.fui-Rating[data-fui-enhance]').forEach(enhanceRating);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/*!
 * Fluent 2 Web の表示の部品の小さな振る舞い（非公式）
 * 元の実装は microsoft/fluentui（MIT License、Copyright (c) Microsoft Corporation）。
 * 基準: @fluentui/react-components 9.75.2（microsoft/fluentui commit f9720c35ba89、2026-11-12）。
 * data-fui-enhance を付けた要素だけを扱う。
 * - Avatar: イニシャル（getInitials.ts）、colorful の色（useAvatar.tsx:31-35、200-242）、
 *   既定のアイコン（PersonRegular）、画像の読み込みに失敗したときのアイコン（useAvatar.tsx:102-133）
 * - Card: 隠しチェックボックスを持つ選択できるカードの、クリックと Enter での切り替え（useCardSelectable.ts）
 * - AvatarGroupPopover: popover 属性の面の開閉を、トリガーの aria-expanded に写す
 */
(() => {
  'use strict';

  // --- getInitials（react-avatar/library/src/utils/getInitials.ts）---------------------------
  // 正規表現の \u エスケープを避け、文字の範囲を数値で比べる（内容は v9 の正規表現と同じ）

  // 括弧の組とその中身、閉じない括弧の残り（4、71）
  const UNWANTED_ENCLOSURES_REGEX = /[\(\[\{][^\)\]\}]*([\)\]\}]|$)/g;
  // 電話番号（18）
  const PHONENUMBER_REGEX = /^(?:\d[\d\s]*\d|\d[\d\s]*(?:ext|x)\s*\d+)$/i;
  const MULTIPLE_WHITESPACES_REGEX = /\s+/g;

  // UNWANTED_CHARS_REGEX（12）: 制御文字、空白以外の ASCII 記号、U+007B-U+00BF、U+0250-U+036F、U+E000-U+FFFF。
  // v9 の正規表現は u フラグなしなので、UTF-16 のコード単位ごとに判定する
  const isUnwantedCodeUnit = (c) =>
    c <= 0x1f ||
    (c >= 0x21 && c <= 0x2f) ||
    (c >= 0x3a && c <= 0x40) ||
    (c >= 0x5b && c <= 0x60) ||
    (c >= 0x7b && c <= 0xbf) ||
    (c >= 0x250 && c <= 0x36f) ||
    (c >= 0xe000 && c <= 0xffff);

  // UNSUPPORTED_TEXT_REGEX（32-33）: アラビア文字、ハングル、ひらがな、カタカナ、CJK 統合漢字。
  // 先頭の 1 文字がこれらならイニシャルを作らない。日本語の名前ではイニシャルが空になる
  const UNSUPPORTED_RANGES = [
    [0x0600, 0x06ff], [0x0750, 0x077f], [0x08a0, 0x08ff],
    [0x1100, 0x11ff], [0x3130, 0x318f], [0xa960, 0xa97f], [0xac00, 0xd7af], [0xd7b0, 0xd7ff],
    [0x3040, 0x309f], [0x30a0, 0x30ff],
    [0x3400, 0x4dbf], [0x4e00, 0x9fff], [0xf900, 0xfaff],
  ];
  const isUnsupportedCodePoint = (cp) => UNSUPPORTED_RANGES.some(([a, b]) => cp >= a && cp <= b);

  const firstCodePoint = (value) => {
    if (!value) return '';
    const cp = value.codePointAt(0);
    return cp === undefined ? '' : String.fromCodePoint(cp);
  };

  const cleanupDisplayName = (name) => {
    let s = name.replace(UNWANTED_ENCLOSURES_REGEX, (match, closing) => (closing ? '' : match));
    let out = '';
    for (let i = 0; i < s.length; i++) {
      if (!isUnwantedCodeUnit(s.charCodeAt(i))) out += s[i];
    }
    s = out.replace(MULTIPLE_WHITESPACES_REGEX, ' ');
    return s.trim();
  };

  const getInitials = (displayName, isRtl, firstInitialOnly) => {
    if (!displayName) return '';
    const name = cleanupDisplayName(displayName);
    const first = firstCodePoint(name);
    // v9 は先頭のコードポイントの文字列（サロゲートペアなら 2 単位）に正規表現を当てる。
    // 範囲はすべて BMP の中なので、補助面の文字は当たらない
    if ((first && isUnsupportedCodePoint(first.codePointAt(0))) || PHONENUMBER_REGEX.test(name)) {
      return '';
    }
    let initials = '';
    const splits = name.split(' ');
    if (splits.length !== 0) initials += firstCodePoint(splits[0]).toUpperCase();
    if (!firstInitialOnly) {
      if (splits.length === 2) initials += firstCodePoint(splits[1]).toUpperCase();
      else if (splits.length === 3) initials += firstCodePoint(splits[2]).toUpperCase();
    }
    if (isRtl && [...initials].length > 1) {
      const chars = [...initials];
      return chars[1] + chars[0];
    }
    return initials;
  };

  // --- colorful の色（useAvatar.tsx:200-242）--------------------------------------------------
  const AVATAR_COLORS = [
    'dark-red', 'cranberry', 'red', 'pumpkin', 'peach', 'marigold', 'gold', 'brass', 'brown', 'forest',
    'seafoam', 'dark-green', 'light-teal', 'teal', 'steel', 'blue', 'royal-blue', 'cornflower', 'navy', 'lavender',
    'purple', 'grape', 'lilac', 'pink', 'magenta', 'plum', 'beige', 'mink', 'platinum', 'anchor',
  ];
  const getHashCode = (str) => {
    let hashCode = 0;
    for (let len = str.length - 1; len >= 0; len--) {
      const ch = str.charCodeAt(len);
      const shift = len % 8;
      hashCode ^= (ch << shift) + (ch >> (8 - shift));
    }
    return hashCode;
  };

  // PersonRegular（@fluentui/svg-icons の person_20_regular）。v9 の react-icons と同じく 1em で描き、icon スロットの font-size で大きさを決める
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const PERSON_PATH = 'M10 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8M7 6a3 3 0 1 1 6 0 3 3 0 0 1-6 0m-2 5a2 2 0 0 0-2 2c0 1.7.83 2.97 2.13 3.8A9 9 0 0 0 10 18c1.85 0 3.58-.39 4.87-1.2A4.4 4.4 0 0 0 17 13a2 2 0 0 0-2-2zm-1 2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1c0 1.3-.62 2.28-1.67 2.95A8 8 0 0 1 10 17a8 8 0 0 1-4.33-1.05A3.4 3.4 0 0 1 4 13';
  const createPersonIcon = () => {
    const span = document.createElement('span');
    span.className = 'fui-Avatar__icon';
    span.setAttribute('aria-hidden', 'true');
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'fui-Icon');
    svg.setAttribute('width', '1em');
    svg.setAttribute('height', '1em');
    svg.setAttribute('viewBox', '0 0 20 20');
    svg.setAttribute('fill', 'currentColor');
    svg.setAttribute('aria-hidden', 'true');
    const path = document.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', PERSON_PATH);
    svg.appendChild(path);
    span.appendChild(svg);
    return span;
  };

  let uid = 0;
  const enhanceAvatar = (el) => {
    // 名前は data-name。なければ aria-label を使う
    const name = el.getAttribute('data-name') ?? el.getAttribute('aria-label') ?? '';
    const size = Number(el.getAttribute('data-size') || 32);
    const isRtl = getComputedStyle(el).direction === 'rtl';

    // colorful: idForColor（data-id-for-color）か name のハッシュで 30 色から選ぶ
    if (el.getAttribute('data-color') === 'colorful') {
      const key = el.getAttribute('data-id-for-color') ?? name;
      el.setAttribute('data-resolved-color', AVATAR_COLORS[getHashCode(key) % AVATAR_COLORS.length]);
    }

    if (!el.getAttribute('role')) el.setAttribute('role', 'img');
    if (!el.id) el.id = `fui-avatar-${++uid}`;

    // initials: 書かれていなければ name から作る。空なら描かない（useAvatar.tsx:37-47、108-121）
    let initials = el.querySelector(':scope > .fui-Avatar__initials');
    if (!initials) {
      const text = getInitials(name, isRtl, size <= 16);
      if (text) {
        initials = document.createElement('span');
        initials.className = 'fui-Avatar__initials';
        initials.id = `${el.id}__initials`;
        initials.textContent = text;
        el.prepend(initials);
      }
    }

    // icon: initials も表示できる画像もないときだけ（useAvatar.tsx:123-133）
    const image = el.querySelector(':scope > .fui-Avatar__image');
    const ensureIcon = () => {
      if (initials || el.querySelector(':scope > .fui-Avatar__icon')) return;
      const icon = createPersonIcon();
      if (image) image.after(icon);
      else el.prepend(icon);
    };
    const removeIcon = () => {
      const icon = el.querySelector(':scope > .fui-Avatar__icon');
      if (icon && !initials) icon.remove();
    };
    if (image) {
      image.addEventListener('error', () => {
        image.hidden = true;
        ensureIcon();
      });
      image.addEventListener('load', () => {
        image.hidden = false;
        removeIcon();
      });
      if (image.complete && image.naturalWidth === 0 && image.getAttribute('src')) {
        image.hidden = true;
        ensureIcon();
      }
    } else {
      ensureIcon();
    }

    // 名前: aria-label も aria-labelledby もなければ、name を aria-label にする（useAvatar.tsx:142-170）
    if (!el.hasAttribute('aria-label') && !el.hasAttribute('aria-labelledby')) {
      const badge = el.querySelector(':scope > .fui-Avatar__badge');
      if (badge && !badge.id) badge.id = `${el.id}__badge`;
      if (name) {
        el.setAttribute('aria-label', name);
        if (badge) el.setAttribute('aria-labelledby', `${el.id} ${badge.id}`);
      } else if (initials) {
        el.setAttribute('aria-labelledby', initials.id + (badge ? ` ${badge.id}` : ''));
      }
      const active = el.getAttribute('data-active');
      if (active === 'active' || active === 'inactive') {
        if (el.hasAttribute('aria-labelledby')) {
          const span = document.createElement('span');
          span.hidden = true;
          span.id = `${el.id}__active`;
          span.textContent = active;
          el.append(span);
          el.setAttribute('aria-labelledby', `${el.getAttribute('aria-labelledby')} ${span.id}`);
        } else if (el.hasAttribute('aria-label')) {
          el.setAttribute('aria-label', `${el.getAttribute('aria-label')} ${active}`);
        }
      }
    }
  };

  // --- Card の選択（useCardSelectable.ts、useCard.ts:65-77）--------------------------------
  const FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]';
  const enhanceCard = (card) => {
    const checkbox = card.querySelector(':scope > .fui-Card__checkbox');
    if (!checkbox) return;
    const toggle = (event) => {
      if (card.getAttribute('aria-disabled') === 'true' || checkbox.disabled) return;
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event('input', { bubbles: true }));
      checkbox.dispatchEvent(new Event('change', { bubbles: true }));
      event.preventDefault();
    };
    card.addEventListener('click', (event) => {
      // チェックボックス自身のクリックはブラウザが切り替える。中の操作できる要素では切り替えない
      if (event.target === checkbox) return;
      const focusable = event.target.closest(FOCUSABLE);
      if (focusable && focusable !== card && card.contains(focusable)) return;
      toggle(event);
    });
    card.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      const focusable = event.target.closest(FOCUSABLE);
      if (focusable && focusable !== checkbox && focusable !== card) return;
      toggle(event);
    });
  };

  // --- AvatarGroupPopover の aria-expanded ------------------------------------------------------
  const enhanceTrigger = (button) => {
    const id = button.getAttribute('popovertarget');
    const surface = id && document.getElementById(id);
    if (!surface) return;
    button.setAttribute('aria-expanded', 'false');
    surface.addEventListener('toggle', (event) => {
      button.setAttribute('aria-expanded', String(event.newState === 'open'));
    });
  };

  /* ProgressBar: aria-valuenow と aria-valuemax から幅を計算し、根の --fui-ProgressBar--value に CSSOM で書く。
     v9 の useProgressBarStyles.styles.ts:126-129 と同じ式。CSSOM の書き込みは CSP（style-src 'self'）の下でも効く */
  const setupProgressBar = (bar) => {
    const now = parseFloat(bar.getAttribute('aria-valuenow'));
    if (Number.isNaN(now)) return;
    const rawMax = parseFloat(bar.getAttribute('aria-valuemax'));
    const max = Number.isNaN(rawMax) || rawMax <= 0 ? 1 : rawMax; // clampMax と同じく、0 以下は 1 にする
    bar.style.setProperty('--fui-ProgressBar--value', `${Math.min(100, Math.max(0, (now / max) * 100))}%`);
  };

  const init = () => {
    document.querySelectorAll('.fui-Avatar[data-fui-enhance]').forEach(enhanceAvatar);
    document.querySelectorAll('.fui-Card[data-fui-enhance]').forEach(enhanceCard);
    document.querySelectorAll('.fui-ProgressBar[data-fui-enhance], [data-fui-enhance] .fui-ProgressBar').forEach(setupProgressBar);
    document.querySelectorAll('.fui-AvatarGroupPopover__triggerButton[data-fui-enhance]').forEach(enhanceTrigger);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/*!
 * Fluent 2 Web のナビゲーションと表の部品の小さな振る舞い（非公式）
 * CSS だけで表せない振る舞いを、data-fui-enhance を付けた要素にだけ足す。依存なし、ES2020。
 * - TabList: クリックと矢印キーでの選択、ローヴィング tabindex、下線のスライド（v9 の FLIP）、タブパネルの切り替え
 * - Tree: 枝の開閉、矢印キー・Home・End・先頭文字での移動、ローヴィング tabindex
 * - Accordion: multiple・collapsible の既定（v9 は複数を開かず、最後の 1 つを閉じさせない）、disabled の summary
 * - Nav: 矢印キーでの移動、選択（aria-current）の付け替え、閉じたカテゴリーへの aria-current
 * - Carousel: 前後のボタンとステップの表示でのスクロール、表示中のカードとの同期
 * 元の実装は microsoft/fluentui（MIT License、Copyright (c) Microsoft Corporation）。
 * 基準: @fluentui/react-components 9.75.2（microsoft/fluentui commit f9720c35ba89、2026-11-12）。
 */
(function () {
  'use strict';

  // 矢印キーでの移動の共通処理: items の中で、current から delta だけ進んだ要素を返す（circular なら端で回る）
  function step(items, current, delta, circular) {
    const i = items.indexOf(current);
    let n = i + delta;
    if (circular) n = (n + items.length) % items.length;
    else n = Math.max(0, Math.min(items.length - 1, n));
    return items[n];
  }

  // ---- TabList（packages/react-components/react-tabs/library/src/components/TabList/useTabList.ts:154-158 の
  //      Tabster の矢印キーのグループ: circular、memorizeCurrent: false、選択中のタブが既定のフォーカス先） ----
  function enhanceTabList(list) {
    const vertical = list.hasAttribute('data-vertical');
    const tabs = () => Array.from(list.querySelectorAll(':scope > .fui-Tab'));
    const enabled = () => tabs().filter((t) => !t.disabled);

    function syncTabIndex() {
      const all = tabs();
      const selected = all.find((t) => t.getAttribute('aria-selected') === 'true') || enabled()[0];
      all.forEach((t) => { t.tabIndex = t === selected ? 0 : -1; });
    }

    function panelOf(tab) {
      const id = tab.getAttribute('aria-controls');
      return id ? document.getElementById(id) : null;
    }

    // 位置は親を基準に測る（useTabAnimatedIndicator.ts:52-65）
    function rect(el) {
      const p = el.parentElement.getBoundingClientRect();
      const r = el.getBoundingClientRect();
      return { x: r.left - p.left, y: r.top - p.top, width: r.width, height: r.height };
    }

    function select(next) {
      const prev = tabs().find((t) => t.getAttribute('aria-selected') === 'true');
      if (!next || next === prev || next.disabled) return;
      const from = prev ? rect(prev) : null;
      if (prev) {
        prev.setAttribute('aria-selected', 'false');
        const pp = panelOf(prev);
        if (pp) pp.hidden = true;
      }
      next.setAttribute('aria-selected', 'true');
      const np = panelOf(next);
      if (np) np.hidden = false;
      syncTabIndex();
      if (!from) return;
      // FLIP: 前のタブの位置へ一瞬で移し（transition なし）、次のフレームで 0 と 1 に戻して滑らせる（96-108, 124）
      const to = rect(next);
      const offset = vertical ? from.y - to.y : from.x - to.x;
      const scale = vertical ? from.height / to.height : from.width / to.width;
      next.setAttribute('data-fui-indicator-jump', '');
      next.style.setProperty('--fui-Tab__indicator--offset', offset + 'px');
      next.style.setProperty('--fui-Tab__indicator--scale', String(scale));
      // 跳んだ位置でスタイルを一度確定させ、そこから戻す。v9 は requestAnimationFrame で戻すが、
      // 画面に出ていないタブでは rAF が止まり下線が残るので、スタイルの確定で代える
      void getComputedStyle(next, '::after').transform;
      next.removeAttribute('data-fui-indicator-jump');
      next.style.setProperty('--fui-Tab__indicator--offset', '0px');
      next.style.setProperty('--fui-Tab__indicator--scale', '1');
    }

    list.addEventListener('click', (ev) => {
      const tab = ev.target.closest('.fui-Tab');
      if (tab && list.contains(tab)) select(tab);
    });
    list.addEventListener('focusin', (ev) => {
      // selectTabOnFocus（TabList.types.ts:82、既定 false）
      if (list.hasAttribute('data-select-tab-on-focus')) {
        const tab = ev.target.closest('.fui-Tab');
        if (tab) select(tab);
      }
    });
    list.addEventListener('keydown', (ev) => {
      const prevKey = vertical ? 'ArrowUp' : 'ArrowLeft';
      const nextKey = vertical ? 'ArrowDown' : 'ArrowRight';
      const rtl = !vertical && getComputedStyle(list).direction === 'rtl';
      const items = enabled();
      const cur = document.activeElement;
      if (!items.includes(cur)) return;
      let target = null;
      if (ev.key === nextKey) target = step(items, cur, rtl ? -1 : 1, true);
      else if (ev.key === prevKey) target = step(items, cur, rtl ? 1 : -1, true);
      else if (ev.key === 'Home') target = items[0];
      else if (ev.key === 'End') target = items[items.length - 1];
      if (target) {
        ev.preventDefault();
        tabs().forEach((t) => { t.tabIndex = t === target ? 0 : -1; });
        target.focus();
      }
    });
    list.addEventListener('focusout', (ev) => {
      if (!list.contains(ev.relatedTarget)) syncTabIndex();
    });
    syncTabIndex();
  }

  // ---- Tree（packages/react-components/react-tree/library/src/utils/tokens.ts の操作:
  //      ArrowUp・ArrowDown・ArrowLeft・ArrowRight・Home・End・Enter と先頭文字の検索） ----
  function enhanceTree(tree) {
    const visibleItems = () => Array.from(tree.querySelectorAll('.fui-TreeItem')).filter((item) => {
      for (let p = item.parentElement.closest('.fui-TreeItem'); p && tree.contains(p); p = p.parentElement.closest('.fui-TreeItem')) {
        if (p.getAttribute('aria-expanded') === 'false') return false;
      }
      return true;
    });
    const isBranch = (item) => item.hasAttribute('aria-expanded');
    const parentItem = (item) => {
      const p = item.parentElement.closest('.fui-TreeItem');
      return p && tree.contains(p) ? p : null;
    };
    const firstChild = (item) => item.querySelector(':scope > .fui-Tree > .fui-TreeItem');

    function focusItem(item) {
      if (!item) return;
      tree.querySelectorAll('.fui-TreeItem').forEach((t) => { t.tabIndex = t === item ? 0 : -1; });
      item.focus();
    }
    function toggle(item, open) {
      if (!isBranch(item)) return;
      const next = open === undefined ? item.getAttribute('aria-expanded') !== 'true' : open;
      item.setAttribute('aria-expanded', String(next));
    }

    tree.addEventListener('click', (ev) => {
      const layout = ev.target.closest('.fui-TreeItemLayout');
      if (!layout || ev.target.closest('.fui-TreeItemLayout__actions')) return;
      const item = layout.parentElement;
      if (!item.classList.contains('fui-TreeItem')) return;
      toggle(item);
      focusItem(item);
    });
    tree.addEventListener('keydown', (ev) => {
      const item = document.activeElement;
      if (!item || !item.classList || !item.classList.contains('fui-TreeItem') || !tree.contains(item)) return;
      const items = visibleItems();
      const rtl = getComputedStyle(tree).direction === 'rtl';
      const openKey = rtl ? 'ArrowLeft' : 'ArrowRight';
      const closeKey = rtl ? 'ArrowRight' : 'ArrowLeft';
      let handled = true;
      if (ev.key === 'ArrowDown') focusItem(step(items, item, 1, false));
      else if (ev.key === 'ArrowUp') focusItem(step(items, item, -1, false));
      else if (ev.key === 'Home') focusItem(items[0]);
      else if (ev.key === 'End') focusItem(items[items.length - 1]);
      else if (ev.key === openKey) {
        if (isBranch(item) && item.getAttribute('aria-expanded') !== 'true') toggle(item, true);
        else if (isBranch(item)) focusItem(firstChild(item));
      } else if (ev.key === closeKey) {
        if (isBranch(item) && item.getAttribute('aria-expanded') === 'true') toggle(item, false);
        else focusItem(parentItem(item));
      } else if (ev.key === 'Enter') toggle(item);
      else if (ev.key.length === 1 && /\S/.test(ev.key)) {
        // 先頭文字の検索: 今の項目の次から順に探す
        const key = ev.key.toLocaleLowerCase();
        const start = items.indexOf(item);
        const order = items.slice(start + 1).concat(items.slice(0, start + 1));
        const hit = order.find((t) => {
          const main = t.querySelector(':scope > .fui-TreeItemLayout .fui-TreeItemLayout__main');
          return main && main.textContent.trim().toLocaleLowerCase().startsWith(key);
        });
        focusItem(hit);
      } else handled = false;
      if (handled) ev.preventDefault();
    });
    // ローヴィング tabindex の初期化: tabindex="0" がなければ先頭の項目を 0 にする
    const all = Array.from(tree.querySelectorAll('.fui-TreeItem'));
    if (!all.some((t) => t.getAttribute('tabindex') === '0') && all[0]) all[0].tabIndex = 0;
    all.forEach((t) => { if (t.getAttribute('tabindex') !== '0') t.tabIndex = -1; });
  }

  // ---- Accordion（packages/react-components/react-accordion/library/src/components/Accordion/useAccordion.ts:55-56:
  //      multiple の既定は false、collapsible の既定は false） ----
  function enhanceAccordion(acc) {
    const multiple = acc.hasAttribute('data-multiple');
    const collapsible = acc.hasAttribute('data-collapsible');
    const items = () => Array.from(acc.querySelectorAll(':scope > .fui-AccordionItem'));

    // 形 A: <details> と <summary>
    acc.addEventListener('click', (ev) => {
      const summary = ev.target.closest('summary.fui-AccordionHeader__button');
      if (!summary || !acc.contains(summary)) return;
      const details = summary.parentElement;
      if (summary.getAttribute('aria-disabled') === 'true') { ev.preventDefault(); return; }
      const openItems = items().filter((d) => d.open);
      // collapsible が false のとき、開いている唯一の項目は閉じない
      if (!collapsible && details.open && openItems.length === 1) { ev.preventDefault(); return; }
      if (!multiple && !details.open && !details.hasAttribute('name')) {
        openItems.forEach((d) => { d.open = false; });
      }
    });

    // 形 B: <button aria-expanded> と、aria-controls で指すパネル（hidden で隠す）
    acc.addEventListener('click', (ev) => {
      const button = ev.target.closest('button.fui-AccordionHeader__button');
      if (!button || !acc.contains(button) || button.disabled) return;
      const all = Array.from(acc.querySelectorAll('button.fui-AccordionHeader__button'));
      const open = button.getAttribute('aria-expanded') === 'true';
      const openCount = all.filter((b) => b.getAttribute('aria-expanded') === 'true').length;
      if (open && !collapsible && openCount === 1) return;
      const set = (b, v) => {
        b.setAttribute('aria-expanded', String(v));
        const panel = document.getElementById(b.getAttribute('aria-controls') || '');
        if (panel) panel.hidden = !v;
      };
      if (!open && !multiple) all.forEach((b) => { if (b !== button) set(b, false); });
      set(button, !open);
    });
  }

  // ---- Nav（packages/react-components/react-nav/library/src/components/NavDrawerBody/useNavDrawerBody.ts:23-26:
  //      本体は縦・循環の矢印キーのグループ） ----
  function enhanceNav(nav) {
    const focusables = () => Array.from(nav.querySelectorAll('.fui-NavItem, .fui-NavCategoryItem, .fui-NavSubItem'))
      .filter((el) => !el.closest('details:not([open]) > .fui-NavSubItemGroup'));

    // 閉じたカテゴリーの子が選ばれていれば、カテゴリーに aria-current="page" を付ける（useNavCategoryItem.tsx:89-92）
    function syncCategories() {
      nav.querySelectorAll('details.fui-NavCategory').forEach((d) => {
        const summary = d.querySelector(':scope > .fui-NavCategoryItem');
        const childSelected = !!d.querySelector('.fui-NavSubItem[aria-current="page"]');
        if (summary) summary.setAttribute('aria-current', !d.open && childSelected ? 'page' : 'false');
      });
    }

    nav.addEventListener('click', (ev) => {
      const item = ev.target.closest('.fui-NavItem, .fui-NavSubItem');
      if (!item || !nav.contains(item)) return;
      // 設計書の見本などで href="#" のときは移動せず、選択だけを付け替える
      if (item.getAttribute('href') === '#') ev.preventDefault();
      nav.querySelectorAll('.fui-NavItem, .fui-NavSubItem').forEach((el) => {
        el.setAttribute('aria-current', el === item ? 'page' : 'false');
      });
      syncCategories();
    });
    nav.addEventListener('toggle', syncCategories, true);
    nav.addEventListener('keydown', (ev) => {
      if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return;
      const items = focusables();
      const cur = document.activeElement;
      if (!items.includes(cur)) return;
      ev.preventDefault();
      step(items, cur, ev.key === 'ArrowDown' ? 1 : -1, true).focus();
    });
    syncCategories();
  }

  // ---- Carousel（v9 は Embla Carousel。ここではスクロールスナップの位置を動かすだけの近似） ----
  function enhanceCarousel(car) {
    const viewport = car.querySelector('.fui-CarouselViewport');
    if (!viewport) return;
    const cards = Array.from(car.querySelectorAll('.fui-CarouselCard'));
    const navButtons = Array.from(car.querySelectorAll('.fui-CarouselNavButton, .fui-CarouselNavImageButton'));
    const prev = car.querySelector('.fui-CarouselButton[data-direction="prev"]');
    const next = car.querySelector('.fui-CarouselButton[data-direction="next"]');
    const circular = car.hasAttribute('data-circular');
    let index = 0;

    function goTo(i) {
      const n = circular ? (i + cards.length) % cards.length : Math.max(0, Math.min(cards.length - 1, i));
      const card = cards[n];
      if (!card) return;
      // 今の位置からの差で動かす（RTL では scrollLeft が負になるが、差の足し算はそのまま使える）
      const rtl = getComputedStyle(viewport).direction === 'rtl';
      const v = viewport.getBoundingClientRect();
      const r = card.getBoundingClientRect();
      const delta = rtl ? r.right - v.right : r.left - v.left;
      viewport.scrollTo({ left: viewport.scrollLeft + delta });
    }
    function update(i) {
      index = i;
      navButtons.forEach((b, k) => b.setAttribute('aria-selected', String(k === i)));
      cards.forEach((c, k) => {
        c.toggleAttribute('inert', k !== i && !c.hasAttribute('data-auto-size'));
        c.setAttribute('aria-hidden', String(k !== i));
      });
      // 端では前後のボタンを使えなくする（useCarouselButton.tsx:95-97。循環しないとき）
      [[prev, 0], [next, cards.length - 1]].forEach(([btn, edge]) => {
        if (!btn) return;
        const off = !circular && i === edge;
        btn.disabled = off;
        btn.setAttribute('aria-disabled', String(off));
      });
    }

    if (prev) prev.addEventListener('click', () => goTo(index - 1));
    if (next) next.addEventListener('click', () => goTo(index + 1));
    navButtons.forEach((b, k) => b.addEventListener('click', () => goTo(k)));

    // 表示中のカードを、ビューポートの中央に近いものとして決める
    let raf = 0;
    viewport.addEventListener('scroll', () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const v = viewport.getBoundingClientRect();
        const mid = v.left + v.width / 2;
        let best = 0;
        let dist = Infinity;
        cards.forEach((c, k) => {
          const r = c.getBoundingClientRect();
          const d = Math.abs(r.left + r.width / 2 - mid);
          if (d < dist) { dist = d; best = k; }
        });
        if (best !== index) update(best);
      });
    }, { passive: true });
    update(0);
  }

  function init() {
    document.querySelectorAll('.fui-TabList[data-fui-enhance]').forEach(enhanceTabList);
    document.querySelectorAll('.fui-Tree[role="tree"][data-fui-enhance]').forEach(enhanceTree);
    document.querySelectorAll('.fui-Accordion[data-fui-enhance]').forEach(enhanceAccordion);
    document.querySelectorAll('.fui-NavDrawer[data-fui-enhance], .fui-Nav[data-fui-enhance]').forEach(enhanceNav);
    document.querySelectorAll('.fui-Carousel[data-fui-enhance]').forEach(enhanceCarousel);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();

/*!
 * Fluent 2 Web オーバーレイと通知の小さな振る舞い（非公式）
 * CSS だけで表せない所を補う。属性 data-fui-enhance を付けた要素だけを扱う。
 * 元の実装は microsoft/fluentui（MIT License、Copyright (c) Microsoft Corporation）。
 * 基準: @fluentui/react-components 9.75.2（commit f9720c35ba89、2026-11-12）。依存なし、ES2020。
 *
 * 扱うもの:
 * - Dialog と OverlayDrawer（<dialog data-fui-enhance>）: command="--show" で show()、
 *   commandfor が使えないブラウザーでの代替、modal の外側クリックと non-modal の Esc で閉じる
 * - Drawer（data-fui-enhance）: DrawerBody のスクロール状態を data-scroll-state に書く
 * - Menu（.fui-MenuPopover[popover][data-fui-enhance]）: 矢印キー、Home と End、先頭文字の検索、Tab、項目の選択
 * - Tooltip（.fui-Tooltip__content[popover][data-fui-enhance]）: 表示と非表示の遅延、blur と Esc で消す
 * - Toast（button[data-fui-enhance][data-fui-toast]）: Toaster への追加、自動で消す時間、読み上げ、Esc と矢印キー
 * - MessageBar（data-fui-enhance）: layout="auto" の折り返し、MessageBarGroup の出入りの動き
 */
(() => {
  'use strict';

  const ENHANCE = '[data-fui-enhance]';
  const reduceMotion = () => window.matchMedia('screen and (prefers-reduced-motion: reduce)').matches;

  /* ---------- Dialog と OverlayDrawer ---------- */
  // v9 は modal の backdrop のクリック（useDialogSurface.ts:48-59）と、どの modalType でも Esc（:61-74）で閉じる。
  const hasInvokerCommands = 'commandForElement' in HTMLButtonElement.prototype;
  const hasClosedBy = 'closedBy' in HTMLDialogElement.prototype;

  function runCommand(target, command) {
    if (!(target instanceof HTMLDialogElement)) return;
    if (command === 'show-modal' && !target.open) target.showModal();
    else if (command === '--show' && !target.open) target.show();
    else if (command === 'close' && target.open) target.close();
    else if (command === 'request-close' && target.open) {
      if (typeof target.requestClose === 'function') target.requestClose();
      else target.close();
    }
  }

  function setupDialog(dialog) {
    // non-modal を開くカスタムコマンド（ネイティブの command イベント）
    dialog.addEventListener('command', (ev) => {
      if (ev.command === '--show') runCommand(dialog, '--show');
    });
    const modalType = dialog.getAttribute('data-modal-type') || 'modal';
    // closedby が使えないときの外側クリック。modal だけ閉じる
    if (!hasClosedBy && modalType === 'modal') {
      dialog.addEventListener('click', (ev) => {
        if (ev.target !== dialog) return;
        const r = dialog.getBoundingClientRect();
        const inside = ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom;
        if (!inside) dialog.close();
      });
    }
    // show() で開いた non-modal は、ブラウザーによっては Esc で閉じない。v9 は閉じる
    dialog.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape' && dialog.open && !dialog.matches(':modal')) {
        ev.preventDefault();
        dialog.close();
      }
    });
  }

  // commandfor が使えないブラウザーでは、data-fui-enhance を付けたボタンのクリックで代わりに実行する
  document.addEventListener('click', (ev) => {
    if (hasInvokerCommands) return;
    const button = ev.target instanceof Element ? ev.target.closest('button[commandfor]' + ENHANCE) : null;
    if (!button) return;
    const target = document.getElementById(button.getAttribute('commandfor'));
    runCommand(target, button.getAttribute('command'));
  });

  /* ---------- Drawer のスクロール状態 ---------- */
  // DrawerBody/useDrawerBody.ts:41-55。OVERFLOW_TOLERANCE 1（:27）、SCROLL_BOTTOM_TOLERANCE 2（:33）
  function scrollState(el) {
    const { scrollTop, scrollHeight, clientHeight } = el;
    if (scrollHeight - clientHeight <= 1) return 'none';
    if (scrollTop === 0) return 'top';
    if (scrollHeight - clientHeight - scrollTop <= 2) return 'bottom';
    return 'middle';
  }

  function setupDrawer(drawer) {
    const body = drawer.querySelector('.fui-DrawerBody');
    if (!body) return;
    const update = () => drawer.setAttribute('data-scroll-state', scrollState(body));
    body.addEventListener('scroll', update, { passive: true });
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(body);
    drawer.addEventListener('toggle', update);
    update();
  }

  /* ---------- Menu ---------- */
  // MenuList/useMenuList.ts:49（循環する矢印キー）、MenuItem/useMenuItemBase.tsx:73-121（クリック、hover でのフォーカス、先頭文字の検索）、
  // MenuPopover/useMenuPopover.ts:40-46,99-110（Tab で閉じてトリガーへ戻す）
  const ITEM = '[role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"]';

  function setupMenu(popover) {
    const items = () => Array.from(popover.querySelectorAll(ITEM));
    const trigger = () => (popover.id ? document.querySelector(`[popovertarget="${CSS.escape(popover.id)}"]`) : null);
    const focusItem = (item) => {
      if (!item) return;
      items().forEach((it) => it.setAttribute('tabindex', it === item ? '0' : '-1'));
      item.focus();
    };

    popover.addEventListener('toggle', (ev) => {
      const t = trigger();
      if (t) t.setAttribute('aria-expanded', String(ev.newState === 'open'));
      if (ev.newState === 'open') focusItem(items()[0]);
    });

    popover.addEventListener('keydown', (ev) => {
      const list = items();
      const index = list.indexOf(document.activeElement);
      switch (ev.key) {
        case 'ArrowDown':
          ev.preventDefault();
          focusItem(list[(index + 1) % list.length]);
          return;
        case 'ArrowUp':
          ev.preventDefault();
          focusItem(list[(index - 1 + list.length) % list.length]);
          return;
        case 'Home':
          ev.preventDefault();
          focusItem(list[0]);
          return;
        case 'End':
          ev.preventDefault();
          focusItem(list[list.length - 1]);
          return;
        case 'Tab': {
          ev.preventDefault();
          popover.hidePopover();
          const t = trigger();
          if (t) t.focus();
          return;
        }
        case 'Enter':
        case ' ':
          if (index >= 0) {
            ev.preventDefault();
            list[index].click();
          }
          return;
        default:
          // 先頭文字の検索（大文字と小文字を区別しない）
          if (ev.key.length === 1 && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
            const key = ev.key.toLocaleLowerCase();
            const ordered = list.slice(index + 1).concat(list.slice(0, index + 1));
            const hit = ordered.find((it) => (it.textContent || '').trim().toLocaleLowerCase().startsWith(key));
            if (hit) focusItem(hit);
          }
      }
    });

    // マウスが乗った項目にフォーカスを移す（:79-85）
    popover.addEventListener('pointerover', (ev) => {
      const item = ev.target instanceof Element ? ev.target.closest(ITEM) : null;
      if (item && item !== document.activeElement) focusItem(item);
    });

    popover.addEventListener('click', (ev) => {
      const item = ev.target instanceof Element ? ev.target.closest(ITEM) : null;
      if (!item || item.getAttribute('aria-disabled') === 'true') return;
      const role = item.getAttribute('role');
      if (role === 'menuitemcheckbox') {
        item.setAttribute('aria-checked', String(item.getAttribute('aria-checked') !== 'true'));
      } else if (role === 'menuitemradio') {
        const scope = item.closest('[role="group"]') || popover;
        const name = item.getAttribute('data-name');
        scope.querySelectorAll('[role="menuitemradio"]').forEach((it) => {
          if (it.getAttribute('data-name') === name) it.setAttribute('aria-checked', String(it === item));
        });
      }
      // checkbox は閉じない（persistOnClick: true、MenuItemCheckbox/useMenuItemCheckbox.tsx:45）。
      // ほかは閉じる（persistOnItemClick 既定 false、MenuItem/useMenuItemBase.tsx:87）
      const persist = role === 'menuitemcheckbox' || popover.hasAttribute('data-persist-on-item-click');
      if (!persist) {
        popover.hidePopover();
        const t = trigger();
        if (t) t.focus();
      }
    });

    // トリガーで下矢印を押すと開く（MenuTrigger/useMenuTrigger.ts:84）
    const t = trigger();
    if (t) {
      t.setAttribute('aria-haspopup', 'menu');
      t.setAttribute('aria-expanded', 'false');
      t.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowDown' && !popover.matches(':popover-open')) {
          ev.preventDefault();
          popover.showPopover();
        }
      });
    }
  }

  /* ---------- Tooltip ---------- */
  // useTooltipBase.tsx:56-57（show 250ms、hide 250ms）、:203（別の Tooltip が出ていれば遅延 0）、
  // :245-248（blur ではすぐ消す）、:141-157（Esc で消す）
  let visibleTooltip = null;

  function setupTooltip(tip) {
    if (!tip.id) return;
    const id = CSS.escape(tip.id);
    const targets = document.querySelectorAll(`[aria-describedby~="${id}"], [aria-labelledby~="${id}"]`);
    const showDelay = Number(tip.getAttribute('data-show-delay') ?? 250);
    const hideDelay = Number(tip.getAttribute('data-hide-delay') ?? 250);
    let timer = 0;
    // JS から開く popover には暗黙のアンカーができないので、CSSOM でトリガーと面を結ぶ。
    // style 属性ではなく CSSOM で書くので、CSP（style-src 'self'）の下でも効く
    const anchorName = `--fui-tooltip-${tip.id.replace(/[^A-Za-z0-9_-]/g, '_')}`;
    let current = null;
    const show = () => {
      if (tip.matches(':popover-open')) return;
      if (visibleTooltip && visibleTooltip !== tip) visibleTooltip.hidePopover();
      targets.forEach((t) => { if (t !== current && t.style.getPropertyValue('anchor-name') === anchorName) t.style.removeProperty('anchor-name'); });
      if (current) {
        current.style.setProperty('anchor-name', anchorName);
        tip.style.setProperty('position-anchor', anchorName);
      }
      tip.showPopover();
      visibleTooltip = tip;
    };
    const hide = () => {
      if (tip.matches(':popover-open')) tip.hidePopover();
      if (visibleTooltip === tip) visibleTooltip = null;
    };
    const schedule = (fn, delay) => {
      clearTimeout(timer);
      timer = window.setTimeout(fn, delay);
    };
    targets.forEach((target) => {
      target.addEventListener('pointerenter', () => { current = target; schedule(show, visibleTooltip ? 0 : showDelay); });
      target.addEventListener('pointerleave', () => schedule(hide, hideDelay));
      target.addEventListener('focus', () => { current = target; schedule(show, visibleTooltip ? 0 : showDelay); });
      target.addEventListener('blur', () => {
        clearTimeout(timer);
        hide();
      });
      target.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape' && tip.matches(':popover-open')) {
          ev.preventDefault();
          clearTimeout(timer);
          hide();
        }
      });
    });
    // Tooltip の上にマウスがある間は消さない
    tip.addEventListener('pointerenter', () => clearTimeout(timer));
    tip.addEventListener('pointerleave', () => schedule(hide, hideDelay));
  }

  /* ---------- Toast ---------- */
  // 既定: position bottom-end、timeout 3000、pauseOnHover false（state/vanilla/createToaster.ts:20-31）。
  // bottom は末尾に足し、top は先頭に足す（state/useToaster.ts:194-211）。
  // politeness は info だけ polite、ほかは assertive（ToastContainer/useToastContainer.ts:14-19）
  let toastSeq = 0;

  function liveRegion(toaster, politeness) {
    const cls = politeness === 'polite' ? 'fui-AriaLive__polite' : 'fui-AriaLive__assertive';
    let region = toaster.parentElement.querySelector(`:scope > .${cls}`);
    if (!region) {
      region = document.createElement('div');
      region.className = cls;
      region.setAttribute('aria-live', politeness);
      toaster.insertAdjacentElement('afterend', region);
    }
    return region;
  }

  function dismissToast(container) {
    if (container.getAttribute('data-state') === 'exiting') return;
    container.style.setProperty('--fui-ToastContainer--scroll-height', `${container.scrollHeight}px`);
    container.setAttribute('data-state', 'exiting');
    const done = (ev) => {
      if (ev.target !== container || ev.animationName !== 'fui-ToastContainer-size-exit') return;
      container.remove();
    };
    container.addEventListener('animationend', done);
  }

  function showToast(trigger) {
    const template = document.getElementById(trigger.getAttribute('data-fui-toast'));
    const toaster = document.getElementById(trigger.getAttribute('data-fui-toaster'));
    if (!(template instanceof HTMLTemplateElement) || !toaster) return;
    const toast = template.content.firstElementChild ? template.content.firstElementChild.cloneNode(true) : null;
    if (!toast) return;

    const n = ++toastSeq;
    const container = document.createElement('div');
    container.className = 'fui-ToastContainer';
    container.setAttribute('role', 'listitem');
    container.tabIndex = 0;
    const title = toast.querySelector('.fui-ToastTitle');
    const body = toast.querySelector('.fui-ToastBody');
    if (title) {
      title.id = title.id || `fui-toast-title-${n}`;
      container.setAttribute('aria-labelledby', title.id);
    }
    if (body) {
      body.id = body.id || `fui-toast-body-${n}`;
      container.setAttribute('aria-describedby', body.id);
    }
    container.append(toast);

    const timeout = Number(trigger.getAttribute('data-timeout') ?? toaster.getAttribute('data-timeout') ?? 3000);
    if (timeout >= 0) {
      const timer = document.createElement('span');
      timer.className = 'fui-ToastContainer__timer';
      container.style.setProperty('--fui-ToastContainer--timeout', `${timeout}ms`);
      timer.addEventListener('animationend', () => dismissToast(container));
      container.append(timer);
    }
    if (toaster.hasAttribute('data-pause-on-hover')) {
      container.addEventListener('pointerenter', () => container.setAttribute('data-paused', ''));
      container.addEventListener('pointerleave', () => container.removeAttribute('data-paused'));
    }
    container.addEventListener('click', (ev) => {
      if (ev.target instanceof Element && ev.target.closest('[data-fui-toast-dismiss]')) dismissToast(container);
    });

    const position = toaster.getAttribute('data-position') || 'bottom-end';
    if (position.startsWith('bottom')) toaster.append(container);
    else toaster.prepend(container);

    // 同時に出す数の上限（limit。既定は無制限）
    const limit = Number(toaster.getAttribute('data-limit') || 0);
    if (limit > 0) {
      const live = Array.from(toaster.querySelectorAll(':scope > .fui-ToastContainer:not([data-state="exiting"])'));
      const excess = live.length - limit;
      const oldest = position.startsWith('bottom') ? live.slice(0, excess) : live.slice(live.length - excess);
      if (excess > 0) oldest.forEach(dismissToast);
    }

    // 高さの動きのため、測った高さを渡す
    container.style.setProperty('--fui-ToastContainer--scroll-height', `${container.scrollHeight}px`);
    container.setAttribute('data-state', 'entering');
    container.addEventListener('animationend', (ev) => {
      if (ev.target === container && ev.animationName === 'fui-ToastContainer-fade-in') {
        container.setAttribute('data-state', 'visible');
      }
    });
    if (reduceMotion()) container.setAttribute('data-state', 'visible');

    // 読み上げ
    const intent = toast.getAttribute('data-intent');
    const region = liveRegion(toaster, intent === 'info' || !intent ? 'polite' : 'assertive');
    region.textContent = '';
    window.setTimeout(() => {
      region.textContent = (toast.textContent || '').replace(/\s+/g, ' ').trim();
    }, 50);
  }

  function setupToaster(toaster) {
    toaster.setAttribute('role', 'list');
    // Esc ですべて閉じる（Toaster/useToaster.tsx:36-46）、上下の矢印で移る（useToasterFocusManagement.ts:45-60）
    toaster.addEventListener('keydown', (ev) => {
      const list = Array.from(toaster.querySelectorAll(':scope > .fui-ToastContainer'));
      if (ev.key === 'Escape') {
        ev.preventDefault();
        list.forEach(dismissToast);
      } else if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
        const i = list.indexOf(document.activeElement);
        if (i < 0) return;
        ev.preventDefault();
        const next = list[i + (ev.key === 'ArrowDown' ? 1 : -1)];
        if (next) next.focus();
      }
    });
  }

  document.addEventListener('click', (ev) => {
    const trigger = ev.target instanceof Element ? ev.target.closest('[data-fui-toast]' + ENHANCE) : null;
    if (trigger) showToast(trigger);
  });

  /* ---------- MessageBar ---------- */
  // layout="auto" の折り返し（MessageBar/useMessageBarReflow.ts:19-63）: 幅が scrollWidth より狭くなったら複数行にし、
  // 単一行の幅まで広がったら戻す
  function setupMessageBar(bar) {
    // 閉じるボタン（data-fui-dismiss）。MessageBarGroup の中では退場の動きのあとで外す
    bar.addEventListener('click', (ev) => {
      if (!(ev.target instanceof Element) || !ev.target.closest('[data-fui-dismiss]')) return;
      if (bar.parentElement && bar.parentElement.classList.contains('fui-MessageBarGroup') && !reduceMotion()) {
        bar.setAttribute('data-state', 'exiting');
        bar.addEventListener('animationend', () => bar.remove(), { once: true });
      } else {
        bar.remove();
      }
    });

    const layout = bar.getAttribute('data-layout');
    if (layout && layout !== 'auto') return;
    if (!('ResizeObserver' in window)) return;
    let reflowing = false;
    let singleLineWidth = 0;
    const apply = () => {
      if (reflowing) {
        bar.setAttribute('data-computed-layout', 'multiline');
        if (!bar.querySelector(':scope > .fui-MessageBar__bottomReflowSpacer')) {
          const spacer = document.createElement('div');
          spacer.className = 'fui-MessageBar__bottomReflowSpacer';
          bar.append(spacer);
        }
      } else {
        bar.removeAttribute('data-computed-layout');
        const spacer = bar.querySelector(':scope > .fui-MessageBar__bottomReflowSpacer');
        if (spacer) spacer.remove();
      }
    };
    new ResizeObserver((entries) => {
      const entry = entries[0];
      const inlineSize = entry.borderBoxSize && entry.borderBoxSize[0] ? entry.borderBoxSize[0].inlineSize : bar.getBoundingClientRect().width;
      let next = reflowing;
      if (reflowing) {
        if (inlineSize >= singleLineWidth) next = false;
      } else if (inlineSize < bar.scrollWidth) {
        next = true;
        singleLineWidth = bar.scrollWidth;
      }
      if (next !== reflowing) {
        reflowing = next;
        apply();
      }
    }).observe(bar);
  }

  /* ---------- 起動 ---------- */
  function init(root) {
    root.querySelectorAll('dialog.fui-DialogSurface' + ENHANCE + ', dialog.fui-OverlayDrawer' + ENHANCE).forEach(setupDialog);
    root.querySelectorAll('.fui-OverlayDrawer' + ENHANCE + ', .fui-InlineDrawer' + ENHANCE).forEach(setupDrawer);
    root.querySelectorAll('.fui-MenuPopover[popover]' + ENHANCE).forEach(setupMenu);
    root.querySelectorAll('.fui-Tooltip__content[popover]' + ENHANCE).forEach(setupTooltip);
    root.querySelectorAll('.fui-Toaster' + ENHANCE).forEach(setupToaster);
    root.querySelectorAll('.fui-MessageBar' + ENHANCE).forEach(setupMessageBar);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init(document));
  else init(document);
})();
