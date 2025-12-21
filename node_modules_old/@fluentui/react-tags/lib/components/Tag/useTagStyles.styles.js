'use client';

import { __resetStyles, __styles, mergeClasses, shorthands } from '@griffel/react';
import { tokens, typographyStyles } from '@fluentui/react-theme';
import { createCustomFocusIndicatorStyle } from '@fluentui/react-tabster';
export const tagClassNames = {
  root: 'fui-Tag',
  media: 'fui-Tag__media',
  icon: 'fui-Tag__icon',
  primaryText: 'fui-Tag__primaryText',
  secondaryText: 'fui-Tag__secondaryText',
  dismissIcon: 'fui-Tag__dismissIcon'
};
/**
 * Inner horizontal space left and right of Tag
 */
const tagSpacingMedium = '7px';
const tagSpacingSmall = '5px';
const tagSpacingExtraSmall = '5px';
const mediumIconSize = '20px';
const smallIconSize = '16px';
const extraSmallIconSize = '12px';
const baseStyles = {
  // reset default button style:
  fontFamily: 'inherit',
  padding: '0px',
  appearance: 'button',
  textAlign: 'unset',
  display: 'inline-grid',
  alignItems: 'center',
  gridTemplateAreas: `
  "media primary   dismissIcon"
  "media secondary dismissIcon"
  `,
  boxSizing: 'border-box',
  width: 'fit-content',
  border: `${tokens.strokeWidthThin} solid ${tokens.colorTransparentStroke}`
};
const useRootRoundedBaseClassName = /*#__PURE__*/__resetStyles("r18f5o0q", "r1u2q8zc", {
  r: [".r18f5o0q{font-family:inherit;padding:0px;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;display:inline-grid;align-items:center;grid-template-areas:\"media primary   dismissIcon\" \"media secondary dismissIcon\";box-sizing:border-box;width:fit-content;border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusMedium);}", ".r18f5o0q[data-fui-focus-visible]{border-radius:var(--borderRadiusMedium);outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);}", ".r1u2q8zc{font-family:inherit;padding:0px;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;display:inline-grid;align-items:center;grid-template-areas:\"media primary   dismissIcon\" \"media secondary dismissIcon\";box-sizing:border-box;width:fit-content;border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusMedium);}", ".r1u2q8zc[data-fui-focus-visible]{border-radius:var(--borderRadiusMedium);outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);}"],
  s: ["@media (forced-colors: active){.r18f5o0q{position:relative;}.r18f5o0q::before{content:\"\";border-top:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-top-left-radius:var(--borderRadiusMedium);border-top-right-radius:var(--borderRadiusMedium);}}", "@media (forced-colors: active){.r1u2q8zc{position:relative;}.r1u2q8zc::before{content:\"\";border-top:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-top-right-radius:var(--borderRadiusMedium);border-top-left-radius:var(--borderRadiusMedium);}}"]
});
const useRootCircularBaseClassName = /*#__PURE__*/__resetStyles("r1mko7zc", "r1wx1e29", {
  r: [".r1mko7zc{font-family:inherit;padding:0px;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;display:inline-grid;align-items:center;grid-template-areas:\"media primary   dismissIcon\" \"media secondary dismissIcon\";box-sizing:border-box;width:fit-content;border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusCircular);}", ".r1mko7zc[data-fui-focus-visible]{border-radius:var(--borderRadiusCircular);outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);}", ".r1wx1e29{font-family:inherit;padding:0px;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;display:inline-grid;align-items:center;grid-template-areas:\"media primary   dismissIcon\" \"media secondary dismissIcon\";box-sizing:border-box;width:fit-content;border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusCircular);}", ".r1wx1e29[data-fui-focus-visible]{border-radius:var(--borderRadiusCircular);outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);}"],
  s: ["@media (forced-colors: active){.r1mko7zc{position:relative;}.r1mko7zc::before{content:\"\";border-top:var(--strokeWidthThin) solid;border-left:var(--strokeWidthThin) solid;border-right:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-radius:var(--borderRadiusCircular);}}", "@media (forced-colors: active){.r1wx1e29{position:relative;}.r1wx1e29::before{content:\"\";border-top:var(--strokeWidthThin) solid;border-right:var(--strokeWidthThin) solid;border-left:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-radius:var(--borderRadiusCircular);}}"]
});
const useRootStyles = /*#__PURE__*/__styles({
  filled: {
    De3pzq: "f16xq7d1",
    sj55zd: "fkfq4zb"
  },
  outline: {
    De3pzq: "fhovq9v",
    sj55zd: "fkfq4zb",
    g2u3we: "fj3muxo",
    h3c5rm: ["f1akhkt", "f1lxtadh"],
    B9xav0g: "f1aperda",
    zhjwy3: ["f1lxtadh", "f1akhkt"]
  },
  brand: {
    De3pzq: "f16xkysk",
    sj55zd: "faj9fo0"
  },
  selected: {
    De3pzq: "ffp7eso",
    sj55zd: "f1phragk",
    g2u3we: "fk9qgl1",
    h3c5rm: ["f1vfbj5f", "f1qpacp7"],
    B9xav0g: "fdf0ba2",
    zhjwy3: ["f1qpacp7", "f1vfbj5f"],
    B8gzw0y: "f1h3a8gf",
    By8wz76: "f1nz3ub2",
    B7iucu3: "fqc85l4"
  },
  medium: {
    Bqenvij: "f1d2rq10"
  },
  small: {
    Bqenvij: "frvgh55"
  },
  "extra-small": {
    qhf8xq: "f10pi13n",
    Bqenvij: "fjamq6b",
    Ie5t1m: "fru8nlv",
    G6hvz8: "f5nasji",
    wgw0td: "f45hpys",
    Bbwa3xj: ["f1sbfcjn", "f1le4i14"],
    m3mfg4: "fq6y7a1",
    B9s7hj8: "f1jr4pq3",
    B9e1dac: "f1tfer7m"
  }
}, {
  d: [".f16xq7d1{background-color:var(--colorNeutralBackground3);}", ".fkfq4zb{color:var(--colorNeutralForeground2);}", ".fhovq9v{background-color:var(--colorSubtleBackground);}", ".fj3muxo{border-top-color:var(--colorNeutralStroke1);}", ".f1akhkt{border-right-color:var(--colorNeutralStroke1);}", ".f1lxtadh{border-left-color:var(--colorNeutralStroke1);}", ".f1aperda{border-bottom-color:var(--colorNeutralStroke1);}", ".f16xkysk{background-color:var(--colorBrandBackground2);}", ".faj9fo0{color:var(--colorBrandForeground2);}", ".ffp7eso{background-color:var(--colorBrandBackground);}", ".f1phragk{color:var(--colorNeutralForegroundOnBrand);}", ".fk9qgl1{border-top-color:var(--colorBrandStroke1);}", ".f1vfbj5f{border-right-color:var(--colorBrandStroke1);}", ".f1qpacp7{border-left-color:var(--colorBrandStroke1);}", ".fdf0ba2{border-bottom-color:var(--colorBrandStroke1);}", ".f1d2rq10{height:32px;}", ".frvgh55{height:24px;}", ".f10pi13n{position:relative;}", ".fjamq6b{height:20px;}"],
  m: [["@media (forced-colors: active){.f1h3a8gf{forced-color-adjust:none;}}", {
    m: "(forced-colors: active)"
  }], ["@media (forced-colors: active){.f1nz3ub2{background-color:Highlight;}}", {
    m: "(forced-colors: active)"
  }], ["@media (forced-colors: active){.fqc85l4{color:HighlightText;}}", {
    m: "(forced-colors: active)"
  }], ["@media (forced-colors: none){.fru8nlv:before,.fru8nlv:after{content:\"\";}}", {
    m: "(forced-colors: none)"
  }], ["@media (forced-colors: none){.f5nasji:before,.f5nasji:after{position:absolute;}}", {
    m: "(forced-colors: none)"
  }], ["@media (forced-colors: none){.f45hpys:before,.f45hpys:after{height:2px;}}", {
    m: "(forced-colors: none)"
  }], ["@media (forced-colors: none){.f1le4i14:before,.f1le4i14:after{right:0;}.f1sbfcjn:before,.f1sbfcjn:after{left:0;}}", {
    m: "(forced-colors: none)"
  }], ["@media (forced-colors: none){.fq6y7a1:before,.fq6y7a1:after{width:100%;}}", {
    m: "(forced-colors: none)"
  }], ["@media (forced-colors: none){.f1jr4pq3:before{bottom:100%;}}", {
    m: "(forced-colors: none)"
  }], ["@media (forced-colors: none){.f1tfer7m:after{top:100%;}}", {
    m: "(forced-colors: none)"
  }]]
});
const useRootDisabledStyles = /*#__PURE__*/__styles({
  filled: {
    Bceei9c: "fdrzuqr",
    De3pzq: "f1bg9a2p",
    sj55zd: "f1s2aq7o",
    g2u3we: "fgig46g",
    h3c5rm: ["f1mxt3zg", "fziff3p"],
    B9xav0g: "f250w3l",
    zhjwy3: ["fziff3p", "f1mxt3zg"]
  },
  outline: {
    Bceei9c: "fdrzuqr",
    De3pzq: "fhovq9v",
    sj55zd: "f1s2aq7o",
    g2u3we: "f1jj8ep1",
    h3c5rm: ["f15xbau", "fy0fskl"],
    B9xav0g: "f4ikngz",
    zhjwy3: ["fy0fskl", "f15xbau"]
  },
  brand: {
    Bceei9c: "fdrzuqr",
    De3pzq: "f1bg9a2p",
    sj55zd: "f1s2aq7o",
    g2u3we: "fgig46g",
    h3c5rm: ["f1mxt3zg", "fziff3p"],
    B9xav0g: "f250w3l",
    zhjwy3: ["fziff3p", "f1mxt3zg"]
  }
}, {
  d: [".fdrzuqr{cursor:not-allowed;}", ".f1bg9a2p{background-color:var(--colorNeutralBackgroundDisabled);}", ".f1s2aq7o{color:var(--colorNeutralForegroundDisabled);}", ".fgig46g{border-top-color:var(--colorTransparentStrokeDisabled);}", ".f1mxt3zg{border-right-color:var(--colorTransparentStrokeDisabled);}", ".fziff3p{border-left-color:var(--colorTransparentStrokeDisabled);}", ".f250w3l{border-bottom-color:var(--colorTransparentStrokeDisabled);}", ".fhovq9v{background-color:var(--colorSubtleBackground);}", ".f1jj8ep1{border-top-color:var(--colorNeutralStrokeDisabled);}", ".f15xbau{border-right-color:var(--colorNeutralStrokeDisabled);}", ".fy0fskl{border-left-color:var(--colorNeutralStrokeDisabled);}", ".f4ikngz{border-bottom-color:var(--colorNeutralStrokeDisabled);}"]
});
/**
 * Styles for root slot when Tag is without leading media/icon
 */
const useRootWithoutMediaStyles = /*#__PURE__*/__styles({
  medium: {
    uwmqm3: ["f1rtp3s9", "f18k1jr3"]
  },
  small: {
    uwmqm3: ["f15vdbe4", "fwiuce9"]
  },
  "extra-small": {
    uwmqm3: ["f15vdbe4", "fwiuce9"]
  }
}, {
  d: [".f1rtp3s9{padding-left:7px;}", ".f18k1jr3{padding-right:7px;}", ".f15vdbe4{padding-left:5px;}", ".fwiuce9{padding-right:5px;}"]
});
/**
 * Styles for root slot when Tag is without dismiss icon
 */
const useRootWithoutDismissStyles = /*#__PURE__*/__styles({
  medium: {
    z189sj: ["f18k1jr3", "f1rtp3s9"]
  },
  small: {
    z189sj: ["fwiuce9", "f15vdbe4"]
  },
  "extra-small": {
    z189sj: ["fwiuce9", "f15vdbe4"]
  }
}, {
  d: [".f18k1jr3{padding-right:7px;}", ".f1rtp3s9{padding-left:7px;}", ".fwiuce9{padding-right:5px;}", ".f15vdbe4{padding-left:5px;}"]
});
export const useIconStyles = /*#__PURE__*/__styles({
  base: {
    Bw0ie65: 0,
    Br312pm: 0,
    nk6f5a: 0,
    Ijaq50: 0,
    Bq1tomu: "fujjg13",
    mc9l5x: "f22iagw",
    B7ck84d: "f1e4lqlz"
  },
  medium: {
    uwmqm3: ["f1rtp3s9", "f18k1jr3"],
    z189sj: ["f7x41pl", "fruq291"],
    a9b677: "f64fuq3",
    Be2twd7: "fe5j1ua"
  },
  small: {
    uwmqm3: ["f15vdbe4", "fwiuce9"],
    z189sj: ["ffczdla", "fgiv446"],
    a9b677: "fjw5fx7",
    Be2twd7: "f4ybsrx"
  },
  "extra-small": {
    uwmqm3: ["f15vdbe4", "fwiuce9"],
    z189sj: ["ffczdla", "fgiv446"],
    a9b677: "frx94fk",
    Be2twd7: "f1ugzwwg"
  }
}, {
  d: [[".fujjg13{grid-area:media;}", {
    p: -1
  }], ".f22iagw{display:flex;}", ".f1e4lqlz{box-sizing:content-box;}", ".f1rtp3s9{padding-left:7px;}", ".f18k1jr3{padding-right:7px;}", ".f7x41pl{padding-right:var(--spacingHorizontalXS);}", ".fruq291{padding-left:var(--spacingHorizontalXS);}", ".f64fuq3{width:20px;}", ".fe5j1ua{font-size:20px;}", ".f15vdbe4{padding-left:5px;}", ".fwiuce9{padding-right:5px;}", ".ffczdla{padding-right:var(--spacingHorizontalXXS);}", ".fgiv446{padding-left:var(--spacingHorizontalXXS);}", ".fjw5fx7{width:16px;}", ".f4ybsrx{font-size:16px;}", ".frx94fk{width:12px;}", ".f1ugzwwg{font-size:12px;}"]
});
export const useMediaStyles = /*#__PURE__*/__styles({
  base: {
    Bw0ie65: 0,
    Br312pm: 0,
    nk6f5a: 0,
    Ijaq50: 0,
    Bq1tomu: "fujjg13",
    mc9l5x: "f22iagw",
    uwmqm3: ["f10xn8zz", "f136y8j8"]
  },
  medium: {
    z189sj: ["f1vdfbxk", "f1f5gg8d"]
  },
  small: {
    z189sj: ["fdw0yi8", "fk8j09s"]
  },
  "extra-small": {
    z189sj: ["fdw0yi8", "fk8j09s"]
  }
}, {
  d: [[".fujjg13{grid-area:media;}", {
    p: -1
  }], ".f22iagw{display:flex;}", ".f10xn8zz{padding-left:1px;}", ".f136y8j8{padding-right:1px;}", ".f1vdfbxk{padding-right:var(--spacingHorizontalS);}", ".f1f5gg8d{padding-left:var(--spacingHorizontalS);}", ".fdw0yi8{padding-right:var(--spacingHorizontalSNudge);}", ".fk8j09s{padding-left:var(--spacingHorizontalSNudge);}"]
});
const useDismissIconStyles = /*#__PURE__*/__styles({
  base: {
    Bw0ie65: 0,
    Br312pm: 0,
    nk6f5a: 0,
    Ijaq50: 0,
    Bq1tomu: "f1k1gsvr",
    mc9l5x: "f22iagw",
    Bahaeuw: "f1v3eptx",
    Boo3t63: "f1rfz71x"
  },
  medium: {
    uwmqm3: ["fruq291", "f7x41pl"],
    z189sj: ["f18k1jr3", "f1rtp3s9"],
    Be2twd7: "fe5j1ua"
  },
  small: {
    uwmqm3: ["fgiv446", "ffczdla"],
    z189sj: ["fwiuce9", "f15vdbe4"],
    Be2twd7: "f4ybsrx"
  },
  "extra-small": {
    uwmqm3: ["fgiv446", "ffczdla"],
    z189sj: ["fwiuce9", "f15vdbe4"],
    Be2twd7: "f1ugzwwg"
  },
  filled: {
    eoavqd: "f8491dx",
    Bi91k9c: "f3ymbdj",
    lj723h: "fryz5bw"
  },
  outline: {
    eoavqd: "f8491dx",
    Bi91k9c: "f3ymbdj",
    lj723h: "fryz5bw"
  },
  brand: {
    eoavqd: "f8491dx",
    Bi91k9c: "f3ymbdj",
    lj723h: "fryz5bw"
  },
  selected: {
    Bi91k9c: "f1rq72xc",
    lj723h: "f18otbis"
  }
}, {
  d: [[".f1k1gsvr{grid-area:dismissIcon;}", {
    p: -1
  }], ".f22iagw{display:flex;}", ".fruq291{padding-left:var(--spacingHorizontalXS);}", ".f7x41pl{padding-right:var(--spacingHorizontalXS);}", ".f18k1jr3{padding-right:7px;}", ".f1rtp3s9{padding-left:7px;}", ".fe5j1ua{font-size:20px;}", ".fgiv446{padding-left:var(--spacingHorizontalXXS);}", ".ffczdla{padding-right:var(--spacingHorizontalXXS);}", ".fwiuce9{padding-right:5px;}", ".f15vdbe4{padding-left:5px;}", ".f4ybsrx{font-size:16px;}", ".f1ugzwwg{font-size:12px;}"],
  m: [["@media (forced-colors: active){.f1v3eptx:hover{color:Highlight;}}", {
    m: "(forced-colors: active)"
  }], ["@media (forced-colors: active){.f1rfz71x:active{color:Highlight;}}", {
    m: "(forced-colors: active)"
  }]],
  h: [".f8491dx:hover{cursor:pointer;}", ".f3ymbdj:hover{color:var(--colorCompoundBrandForeground1Hover);}", ".f1rq72xc:hover{color:var(--colorNeutralForegroundOnBrand);}"],
  a: [".fryz5bw:active{color:var(--colorCompoundBrandForeground1Pressed);}", ".f18otbis:active{color:var(--colorNeutralForegroundOnBrand);}"]
});
export const usePrimaryTextStyles = /*#__PURE__*/__styles({
  base: {
    Huce71: "fz5stix",
    uwmqm3: ["fgiv446", "ffczdla"],
    z189sj: ["ffczdla", "fgiv446"]
  },
  medium: {
    Bahqtrf: "fk6fouc",
    Be2twd7: "fkhj508",
    Bhrd7zp: "figsok6",
    Bg96gwp: "f1i3iumi"
  },
  small: {
    Bahqtrf: "fk6fouc",
    Be2twd7: "fy9rknc",
    Bhrd7zp: "figsok6",
    Bg96gwp: "fwrc4pm"
  },
  "extra-small": {
    Bahqtrf: "fk6fouc",
    Be2twd7: "fy9rknc",
    Bhrd7zp: "figsok6",
    Bg96gwp: "fwrc4pm"
  },
  withoutSecondaryText: {
    Br312pm: "faqcfhe",
    Ijaq50: "f1q3ipgb",
    nk6f5a: "fc0ab3q",
    Byoj8tv: "f1g03r3y"
  },
  withSecondaryText: {
    Bw0ie65: 0,
    Br312pm: 0,
    nk6f5a: 0,
    Ijaq50: 0,
    Bq1tomu: "f1ebragv",
    Bahqtrf: "fk6fouc",
    Be2twd7: "fy9rknc",
    Bhrd7zp: "figsok6",
    Bg96gwp: "fwrc4pm",
    B6of3ja: "f1ryq6si"
  }
}, {
  d: [".fz5stix{white-space:nowrap;}", ".fgiv446{padding-left:var(--spacingHorizontalXXS);}", ".ffczdla{padding-right:var(--spacingHorizontalXXS);}", ".fk6fouc{font-family:var(--fontFamilyBase);}", ".fkhj508{font-size:var(--fontSizeBase300);}", ".figsok6{font-weight:var(--fontWeightRegular);}", ".f1i3iumi{line-height:var(--lineHeightBase300);}", ".fy9rknc{font-size:var(--fontSizeBase200);}", ".fwrc4pm{line-height:var(--lineHeightBase200);}", ".faqcfhe{grid-column-start:primary;}", ".f1q3ipgb{grid-row-start:primary;}", ".fc0ab3q{grid-row-end:secondary;}", ".f1g03r3y{padding-bottom:var(--spacingHorizontalXXS);}", [".f1ebragv{grid-area:primary;}", {
    p: -1
  }], ".f1ryq6si{margin-top:-2px;}"]
});
export const useSecondaryTextBaseClassName = /*#__PURE__*/__resetStyles("r7hv1ps", "rnrslm9", [".r7hv1ps{grid-area:secondary;padding-left:var(--spacingHorizontalXXS);padding-right:var(--spacingHorizontalXXS);font-family:var(--fontFamilyBase);font-size:var(--fontSizeBase100);font-weight:var(--fontWeightRegular);line-height:var(--lineHeightBase100);white-space:nowrap;}", ".rnrslm9{grid-area:secondary;padding-right:var(--spacingHorizontalXXS);padding-left:var(--spacingHorizontalXXS);font-family:var(--fontFamilyBase);font-size:var(--fontSizeBase100);font-weight:var(--fontWeightRegular);line-height:var(--lineHeightBase100);white-space:nowrap;}"]);
/**
 * Apply styling to the Tag slots based on the state
 */
export const useTagStyles_unstable = state => {
  'use no memo';

  const rootRoundedBaseClassName = useRootRoundedBaseClassName();
  const rootCircularBaseClassName = useRootCircularBaseClassName();
  const rootStyles = useRootStyles();
  const rootDisabledStyles = useRootDisabledStyles();
  const rootWithoutMediaStyles = useRootWithoutMediaStyles();
  const rootWithoutDismissStyles = useRootWithoutDismissStyles();
  const iconStyles = useIconStyles();
  const mediaStyles = useMediaStyles();
  const dismissIconStyles = useDismissIconStyles();
  const primaryTextStyles = usePrimaryTextStyles();
  const secondaryTextBaseClassName = useSecondaryTextBaseClassName();
  const {
    disabled,
    shape,
    size,
    appearance,
    selected
  } = state;
  state.root.className = mergeClasses(tagClassNames.root, shape === 'rounded' ? rootRoundedBaseClassName : rootCircularBaseClassName, disabled ? rootDisabledStyles[appearance] : rootStyles[appearance], selected && !disabled && rootStyles.selected, rootStyles[size], !state.media && !state.icon && rootWithoutMediaStyles[size], !state.dismissIcon && rootWithoutDismissStyles[size], state.root.className);
  if (state.media) {
    state.media.className = mergeClasses(tagClassNames.media, mediaStyles.base, mediaStyles[size], state.media.className);
  }
  if (state.icon) {
    state.icon.className = mergeClasses(tagClassNames.icon, iconStyles.base, iconStyles[size], state.icon.className);
  }
  if (state.primaryText) {
    state.primaryText.className = mergeClasses(tagClassNames.primaryText, primaryTextStyles.base, primaryTextStyles[size], state.secondaryText ? primaryTextStyles.withSecondaryText : primaryTextStyles.withoutSecondaryText, state.primaryText.className);
  }
  if (state.secondaryText) {
    state.secondaryText.className = mergeClasses(tagClassNames.secondaryText, secondaryTextBaseClassName, state.secondaryText.className);
  }
  if (state.dismissIcon) {
    state.dismissIcon.className = mergeClasses(tagClassNames.dismissIcon, dismissIconStyles.base, dismissIconStyles[size], !disabled && dismissIconStyles[appearance], selected && !disabled && dismissIconStyles.selected, state.dismissIcon.className);
  }
  return state;
};