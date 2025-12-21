'use client';
"use strict";
Object.defineProperty(exports, "__esModule", {
    value: true
});
function _export(target, all) {
    for(var name in all)Object.defineProperty(target, name, {
        enumerable: true,
        get: all[name]
    });
}
_export(exports, {
    interactionTagPrimaryClassNames: function() {
        return interactionTagPrimaryClassNames;
    },
    useInteractionTagPrimaryStyles_unstable: function() {
        return useInteractionTagPrimaryStyles_unstable;
    }
});
const _react = require("@griffel/react");
const _reacttabster = require("@fluentui/react-tabster");
const _reacttheme = require("@fluentui/react-theme");
const _useTagStylesstyles = require("../Tag/useTagStyles.styles");
const interactionTagPrimaryClassNames = {
    root: 'fui-InteractionTagPrimary',
    media: 'fui-InteractionTagPrimary__media',
    icon: 'fui-InteractionTagPrimary__icon',
    primaryText: 'fui-InteractionTagPrimary__primaryText',
    secondaryText: 'fui-InteractionTagPrimary__secondaryText'
};
const baseStyles = {
    // reset default button style:
    color: 'inherit',
    fontFamily: 'inherit',
    padding: '0px',
    borderStyle: 'none',
    appearance: 'button',
    textAlign: 'unset',
    backgroundColor: 'transparent',
    display: 'inline-grid',
    height: '100%',
    alignItems: 'center',
    gridTemplateAreas: `
  "media primary  "
  "media secondary"
  `,
    border: `${_reacttheme.tokens.strokeWidthThin} solid ${_reacttheme.tokens.colorTransparentStroke}`,
    .../*#__PURE__*/ (0, _reacttabster.createCustomFocusIndicatorStyle)({
        outline: `${_reacttheme.tokens.strokeWidthThick} solid ${_reacttheme.tokens.colorStrokeFocus2}`,
        zIndex: 1
    })
};
const useRootRoundedBaseClassName = /*#__PURE__*/ (0, _react.__resetStyles)("r22quyo", "r1yd8tpa", {
    r: [
        ".r22quyo{color:inherit;font-family:inherit;padding:0px;border-style:none;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;background-color:transparent;display:inline-grid;height:100%;align-items:center;grid-template-areas:\"media primary  \" \"media secondary\";border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusMedium);}",
        ".r22quyo[data-fui-focus-visible]{outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);z-index:1;}",
        ".r1yd8tpa{color:inherit;font-family:inherit;padding:0px;border-style:none;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;background-color:transparent;display:inline-grid;height:100%;align-items:center;grid-template-areas:\"media primary  \" \"media secondary\";border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusMedium);}",
        ".r1yd8tpa[data-fui-focus-visible]{outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);z-index:1;}"
    ],
    s: [
        "@media (forced-colors: active){.r22quyo{position:relative;}.r22quyo::before{content:\"\";border-top:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-top-left-radius:var(--borderRadiusMedium);border-top-right-radius:var(--borderRadiusMedium);}}",
        "@media (forced-colors: active){.r1yd8tpa{position:relative;}.r1yd8tpa::before{content:\"\";border-top:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-top-right-radius:var(--borderRadiusMedium);border-top-left-radius:var(--borderRadiusMedium);}}"
    ]
});
const useRootCircularBaseClassName = /*#__PURE__*/ (0, _react.__resetStyles)("r132q0f6", "r15qe99u", {
    r: [
        ".r132q0f6{color:inherit;font-family:inherit;padding:0px;border-style:none;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;background-color:transparent;display:inline-grid;height:100%;align-items:center;grid-template-areas:\"media primary  \" \"media secondary\";border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusCircular);}",
        ".r132q0f6[data-fui-focus-visible]{outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);z-index:1;}",
        ".r15qe99u{color:inherit;font-family:inherit;padding:0px;border-style:none;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;background-color:transparent;display:inline-grid;height:100%;align-items:center;grid-template-areas:\"media primary  \" \"media secondary\";border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-radius:var(--borderRadiusCircular);}",
        ".r15qe99u[data-fui-focus-visible]{outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);z-index:1;}"
    ],
    s: [
        "@media (forced-colors: active){.r132q0f6{position:relative;}.r132q0f6::before{content:\"\";border-top:var(--strokeWidthThin) solid;border-left:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-top-left-radius:var(--borderRadiusCircular);border-bottom-left-radius:var(--borderRadiusCircular);}}",
        "@media (forced-colors: active){.r15qe99u{position:relative;}.r15qe99u::before{content:\"\";border-top:var(--strokeWidthThin) solid;border-right:var(--strokeWidthThin) solid;position:absolute;inset:-1px;border-top-right-radius:var(--borderRadiusCircular);border-bottom-right-radius:var(--borderRadiusCircular);}}"
    ]
});
/**
 * Style override for pseudo element that draws the border for windows high contrast mode
 */ const useRootCircularContrastStyles = /*#__PURE__*/ (0, _react.__styles)({
    withoutSecondaryAction: {
        Bvgf1ty: "f135udas",
        Cqojjj: 0,
        dd5wkx: 0,
        Bdzpf8n: 0,
        ibz501: [
            "f1i3lrd2",
            "fbpt94e"
        ],
        Bs8828g: [
            "f14bn3u",
            "fdhx3t9"
        ],
        Bn0yx1x: [
            "fu87gj3",
            "f631p13"
        ]
    }
}, {
    m: [
        [
            "@media (forced-colors: active){.f135udas{position:relative;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f1i3lrd2::before{border-right:var(--strokeWidthThin) solid transparent;}.fbpt94e::before{border-left:var(--strokeWidthThin) solid transparent;}}",
            {
                p: -1,
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f14bn3u::before{border-top-right-radius:var(--borderRadiusCircular);}.fdhx3t9::before{border-top-left-radius:var(--borderRadiusCircular);}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f631p13::before{border-bottom-left-radius:var(--borderRadiusCircular);}.fu87gj3::before{border-bottom-right-radius:var(--borderRadiusCircular);}}",
            {
                m: "(forced-colors: active)"
            }
        ]
    ]
});
const useRootStyles = /*#__PURE__*/ (0, _react.__styles)({
    filled: {
        De3pzq: "f16xq7d1",
        sj55zd: "fkfq4zb",
        eoavqd: "f8491dx",
        Jwef8y: "f1h648pw",
        Bi91k9c: "fnwyq0v",
        ecr2s2: "fwdzr64",
        lj723h: "flvvhsy",
        Bbkh6qg: "fkiggi6",
        Cnge2b: "f8zknr1"
    },
    outline: {
        De3pzq: "fhovq9v",
        sj55zd: "fkfq4zb",
        g2u3we: "fj3muxo",
        h3c5rm: [
            "f1akhkt",
            "f1lxtadh"
        ],
        B9xav0g: "f1aperda",
        zhjwy3: [
            "f1lxtadh",
            "f1akhkt"
        ],
        eoavqd: "f8491dx",
        Jwef8y: "f1t94bn6",
        Bi91k9c: "fnwyq0v",
        Bk3fhr4: "ft1hn21",
        I6i3kg: "fqbfmpb",
        Bmfj8id: "fuxngvv",
        ecr2s2: "f1wfn5kd",
        lj723h: "flvvhsy",
        Bnrwwps: "fvpl5sy",
        weioyw: "f1xblose",
        Bpre390: "f8upcvr",
        Bbkh6qg: "fkiggi6",
        Cnge2b: "f8zknr1"
    },
    brand: {
        De3pzq: "f16xkysk",
        sj55zd: "faj9fo0",
        eoavqd: "f8491dx",
        Jwef8y: "f1yj72w4",
        Bi91k9c: "f3ymbdj",
        ecr2s2: "fy3sl2y",
        lj723h: "fryz5bw",
        Bbkh6qg: "fkiggi6",
        Cnge2b: "f8zknr1"
    },
    selected: {
        Bgh53k4: 0,
        B2eet1l: 0,
        De3pzq: 0,
        Bcmaq0h: 0,
        gk0gix: 0,
        B20660r: 0,
        B8a6bjv: 0,
        Bpptf2m: 0,
        e5kdtc: 0,
        Bkjc3bi: 0,
        ayd6f0: "f1tdnksq",
        sj55zd: "f1phragk",
        g2u3we: "fk9qgl1",
        h3c5rm: [
            "f1vfbj5f",
            "f1qpacp7"
        ],
        B9xav0g: "fdf0ba2",
        zhjwy3: [
            "f1qpacp7",
            "f1vfbj5f"
        ],
        B8gzw0y: "f1h3a8gf",
        By8wz76: "f1nz3ub2",
        B7iucu3: "fqc85l4",
        Jwef8y: "f15wkkf3",
        Bi91k9c: "f1rq72xc",
        I6i3kg: "f10jvnl4",
        Bbkh6qg: "f1tx4pjd",
        Bahaeuw: "fu37p9p",
        ecr2s2: "fsp1bjw",
        lj723h: "f18otbis",
        weioyw: "f3wpj5r",
        Cnge2b: "f16z8z4r",
        Boo3t63: "f7ydw7o"
    },
    medium: {
        z189sj: [
            "f18k1jr3",
            "f1rtp3s9"
        ]
    },
    small: {
        z189sj: [
            "fwiuce9",
            "f15vdbe4"
        ]
    },
    "extra-small": {
        z189sj: [
            "fwiuce9",
            "f15vdbe4"
        ],
        qhf8xq: "f10pi13n",
        Ie5t1m: "fru8nlv",
        G6hvz8: "f5nasji",
        wgw0td: "f45hpys",
        Bbwa3xj: [
            "f1sbfcjn",
            "f1le4i14"
        ],
        m3mfg4: "fq6y7a1",
        B9s7hj8: "f1jr4pq3",
        B9e1dac: "f1tfer7m"
    }
}, {
    d: [
        ".f16xq7d1{background-color:var(--colorNeutralBackground3);}",
        ".fkfq4zb{color:var(--colorNeutralForeground2);}",
        ".fhovq9v{background-color:var(--colorSubtleBackground);}",
        ".fj3muxo{border-top-color:var(--colorNeutralStroke1);}",
        ".f1akhkt{border-right-color:var(--colorNeutralStroke1);}",
        ".f1lxtadh{border-left-color:var(--colorNeutralStroke1);}",
        ".f1aperda{border-bottom-color:var(--colorNeutralStroke1);}",
        ".f16xkysk{background-color:var(--colorBrandBackground2);}",
        ".faj9fo0{color:var(--colorBrandForeground2);}",
        [
            ".f1tdnksq{background:var(--colorBrandBackground);}",
            {
                p: -2
            }
        ],
        ".f1phragk{color:var(--colorNeutralForegroundOnBrand);}",
        ".fk9qgl1{border-top-color:var(--colorBrandStroke1);}",
        ".f1vfbj5f{border-right-color:var(--colorBrandStroke1);}",
        ".f1qpacp7{border-left-color:var(--colorBrandStroke1);}",
        ".fdf0ba2{border-bottom-color:var(--colorBrandStroke1);}",
        ".f18k1jr3{padding-right:7px;}",
        ".f1rtp3s9{padding-left:7px;}",
        ".fwiuce9{padding-right:5px;}",
        ".f15vdbe4{padding-left:5px;}",
        ".f10pi13n{position:relative;}"
    ],
    h: [
        ".f8491dx:hover{cursor:pointer;}",
        ".f1h648pw:hover{background-color:var(--colorNeutralBackground3Hover);}",
        ".fnwyq0v:hover{color:var(--colorNeutralForeground2Hover);}",
        ".f1t94bn6:hover{background-color:var(--colorSubtleBackgroundHover);}",
        ".ft1hn21:hover .fui-Icon-filled{display:inline;}",
        ".fqbfmpb:hover .fui-Icon-filled{color:var(--colorNeutralForeground2BrandHover);}",
        ".fuxngvv:hover .fui-Icon-regular{display:none;}",
        ".f1yj72w4:hover{background-color:var(--colorBrandBackground2Hover);}",
        ".f3ymbdj:hover{color:var(--colorCompoundBrandForeground1Hover);}",
        ".f15wkkf3:hover{background-color:var(--colorBrandBackgroundHover);}",
        ".f1rq72xc:hover{color:var(--colorNeutralForegroundOnBrand);}",
        ".f10jvnl4:hover .fui-Icon-filled{color:var(--colorNeutralForegroundOnBrand);}"
    ],
    a: [
        ".fwdzr64:active{background-color:var(--colorNeutralBackground3Pressed);}",
        ".flvvhsy:active{color:var(--colorNeutralForeground2Pressed);}",
        ".f1wfn5kd:active{background-color:var(--colorSubtleBackgroundPressed);}",
        ".fvpl5sy:active .fui-Icon-filled{display:inline;}",
        ".f1xblose:active .fui-Icon-filled{color:var(--colorNeutralForeground2BrandPressed);}",
        ".f8upcvr:active .fui-Icon-regular{display:none;}",
        ".fy3sl2y:active{background-color:var(--colorBrandBackground2Pressed);}",
        ".fryz5bw:active{color:var(--colorCompoundBrandForeground1Pressed);}",
        ".fsp1bjw:active{background-color:var(--colorBrandBackgroundPressed);}",
        ".f18otbis:active{color:var(--colorNeutralForegroundOnBrand);}",
        ".f3wpj5r:active .fui-Icon-filled{color:var(--colorNeutralForegroundOnBrand);}"
    ],
    m: [
        [
            "@media (forced-colors: active){.fkiggi6:hover{background-color:HighlightText;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f8zknr1:active{background-color:HighlightText;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f1h3a8gf{forced-color-adjust:none;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f1nz3ub2{background-color:Highlight;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.fqc85l4{color:HighlightText;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f1tx4pjd:hover{background-color:Highlight;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.fu37p9p:hover{color:HighlightText;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f16z8z4r:active{background-color:Highlight;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.f7ydw7o:active{color:HighlightText;}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: none){.fru8nlv:before,.fru8nlv:after{content:\"\";}}",
            {
                m: "(forced-colors: none)"
            }
        ],
        [
            "@media (forced-colors: none){.f5nasji:before,.f5nasji:after{position:absolute;}}",
            {
                m: "(forced-colors: none)"
            }
        ],
        [
            "@media (forced-colors: none){.f45hpys:before,.f45hpys:after{height:2px;}}",
            {
                m: "(forced-colors: none)"
            }
        ],
        [
            "@media (forced-colors: none){.f1le4i14:before,.f1le4i14:after{right:0;}.f1sbfcjn:before,.f1sbfcjn:after{left:0;}}",
            {
                m: "(forced-colors: none)"
            }
        ],
        [
            "@media (forced-colors: none){.fq6y7a1:before,.fq6y7a1:after{width:100%;}}",
            {
                m: "(forced-colors: none)"
            }
        ],
        [
            "@media (forced-colors: none){.f1jr4pq3:before{bottom:100%;}}",
            {
                m: "(forced-colors: none)"
            }
        ],
        [
            "@media (forced-colors: none){.f1tfer7m:after{top:100%;}}",
            {
                m: "(forced-colors: none)"
            }
        ]
    ]
});
const useRootDisabledAppearances = /*#__PURE__*/ (0, _react.__styles)({
    filled: {
        Bceei9c: "fdrzuqr",
        De3pzq: "f1bg9a2p",
        sj55zd: "f1s2aq7o",
        g2u3we: "fgig46g",
        h3c5rm: [
            "f1mxt3zg",
            "fziff3p"
        ],
        B9xav0g: "f250w3l",
        zhjwy3: [
            "fziff3p",
            "f1mxt3zg"
        ]
    },
    outline: {
        Bceei9c: "fdrzuqr",
        De3pzq: "fhovq9v",
        sj55zd: "f1s2aq7o",
        g2u3we: "f1jj8ep1",
        h3c5rm: [
            "f15xbau",
            "fy0fskl"
        ],
        B9xav0g: "f4ikngz",
        zhjwy3: [
            "fy0fskl",
            "f15xbau"
        ]
    },
    brand: {
        Bceei9c: "fdrzuqr",
        De3pzq: "f1bg9a2p",
        sj55zd: "f1s2aq7o",
        g2u3we: "fgig46g",
        h3c5rm: [
            "f1mxt3zg",
            "fziff3p"
        ],
        B9xav0g: "f250w3l",
        zhjwy3: [
            "fziff3p",
            "f1mxt3zg"
        ]
    }
}, {
    d: [
        ".fdrzuqr{cursor:not-allowed;}",
        ".f1bg9a2p{background-color:var(--colorNeutralBackgroundDisabled);}",
        ".f1s2aq7o{color:var(--colorNeutralForegroundDisabled);}",
        ".fgig46g{border-top-color:var(--colorTransparentStrokeDisabled);}",
        ".f1mxt3zg{border-right-color:var(--colorTransparentStrokeDisabled);}",
        ".fziff3p{border-left-color:var(--colorTransparentStrokeDisabled);}",
        ".f250w3l{border-bottom-color:var(--colorTransparentStrokeDisabled);}",
        ".fhovq9v{background-color:var(--colorSubtleBackground);}",
        ".f1jj8ep1{border-top-color:var(--colorNeutralStrokeDisabled);}",
        ".f15xbau{border-right-color:var(--colorNeutralStrokeDisabled);}",
        ".fy0fskl{border-left-color:var(--colorNeutralStrokeDisabled);}",
        ".f4ikngz{border-bottom-color:var(--colorNeutralStrokeDisabled);}"
    ]
});
/**
 * Styles for InteractionTagPrimary without leading media/icon
 */ const useRootWithoutMediaStyles = /*#__PURE__*/ (0, _react.__styles)({
    medium: {
        uwmqm3: [
            "f1rtp3s9",
            "f18k1jr3"
        ]
    },
    small: {
        uwmqm3: [
            "f15vdbe4",
            "fwiuce9"
        ]
    },
    "extra-small": {
        uwmqm3: [
            "f15vdbe4",
            "fwiuce9"
        ]
    }
}, {
    d: [
        ".f1rtp3s9{padding-left:7px;}",
        ".f18k1jr3{padding-right:7px;}",
        ".f15vdbe4{padding-left:5px;}",
        ".fwiuce9{padding-right:5px;}"
    ]
});
/**
 * Styles for InteractionTagPrimary when InteractionTag has a Secondary button
 */ const useRootWithSecondaryActionStyles = /*#__PURE__*/ (0, _react.__styles)({
    base: {
        B7oj6ja: [
            "f3fg2lr",
            "f13av6d4"
        ],
        Bbmb7ep: [
            "fzi6hpg",
            "fyowgf4"
        ],
        vrafjx: [
            "f1n71otn",
            "f1deefiw"
        ],
        B6xbmo0: [
            "f146y5a9",
            "f1k2ftg"
        ],
        kdpuga: [
            "f1ndz5i7",
            "f1co4qro"
        ],
        Bs8828g: [
            "fyvfifd",
            "fbkbt8g"
        ]
    },
    medium: {
        z189sj: [
            "f1vdfbxk",
            "f1f5gg8d"
        ]
    },
    small: {
        z189sj: [
            "fdw0yi8",
            "fk8j09s"
        ]
    },
    "extra-small": {
        z189sj: [
            "fdw0yi8",
            "fk8j09s"
        ]
    }
}, {
    d: [
        ".f3fg2lr{border-top-right-radius:var(--borderRadiusNone);}",
        ".f13av6d4{border-top-left-radius:var(--borderRadiusNone);}",
        ".fzi6hpg{border-bottom-right-radius:var(--borderRadiusNone);}",
        ".fyowgf4{border-bottom-left-radius:var(--borderRadiusNone);}",
        ".f1n71otn{border-right-style:none;}",
        ".f1deefiw{border-left-style:none;}",
        ".f146y5a9[data-fui-focus-visible]{border-top-right-radius:var(--borderRadiusNone);}",
        ".f1k2ftg[data-fui-focus-visible]{border-top-left-radius:var(--borderRadiusNone);}",
        ".f1ndz5i7[data-fui-focus-visible]{border-bottom-right-radius:var(--borderRadiusNone);}",
        ".f1co4qro[data-fui-focus-visible]{border-bottom-left-radius:var(--borderRadiusNone);}",
        ".f1vdfbxk{padding-right:var(--spacingHorizontalS);}",
        ".f1f5gg8d{padding-left:var(--spacingHorizontalS);}",
        ".fdw0yi8{padding-right:var(--spacingHorizontalSNudge);}",
        ".fk8j09s{padding-left:var(--spacingHorizontalSNudge);}"
    ],
    m: [
        [
            "@media (forced-colors: active){.fbkbt8g::before{border-top-left-radius:0;}.fyvfifd::before{border-top-right-radius:0;}}",
            {
                m: "(forced-colors: active)"
            }
        ]
    ]
});
const useInteractionTagPrimaryStyles_unstable = (state)=>{
    'use no memo';
    const rootRoundedBaseClassName = useRootRoundedBaseClassName();
    const rootCircularBaseClassName = useRootCircularBaseClassName();
    const rootStyles = useRootStyles();
    const rootDisabledAppearances = useRootDisabledAppearances();
    const rootWithoutMediaStyles = useRootWithoutMediaStyles();
    const rootWithSecondaryActionStyles = useRootWithSecondaryActionStyles();
    const iconStyles = (0, _useTagStylesstyles.useIconStyles)();
    const mediaStyles = (0, _useTagStylesstyles.useMediaStyles)();
    const primaryTextStyles = (0, _useTagStylesstyles.usePrimaryTextStyles)();
    const secondaryTextBaseClassName = (0, _useTagStylesstyles.useSecondaryTextBaseClassName)();
    const rootCircularContrastStyles = useRootCircularContrastStyles();
    const { disabled, shape, size, appearance, selected } = state;
    state.root.className = (0, _react.mergeClasses)(interactionTagPrimaryClassNames.root, shape === 'rounded' ? rootRoundedBaseClassName : rootCircularBaseClassName, shape === 'circular' && !state.hasSecondaryAction && rootCircularContrastStyles.withoutSecondaryAction, disabled ? rootDisabledAppearances[appearance] : rootStyles[appearance], selected && !disabled && rootStyles.selected, rootStyles[size], !state.media && !state.icon && rootWithoutMediaStyles[size], state.hasSecondaryAction && rootWithSecondaryActionStyles.base, state.hasSecondaryAction && rootWithSecondaryActionStyles[size], state.root.className);
    if (state.media) {
        state.media.className = (0, _react.mergeClasses)(interactionTagPrimaryClassNames.media, mediaStyles.base, mediaStyles[size], state.media.className);
    }
    if (state.icon) {
        state.icon.className = (0, _react.mergeClasses)(interactionTagPrimaryClassNames.icon, iconStyles.base, iconStyles[size], state.icon.className);
    }
    if (state.primaryText) {
        state.primaryText.className = (0, _react.mergeClasses)(interactionTagPrimaryClassNames.primaryText, primaryTextStyles.base, primaryTextStyles[size], state.secondaryText ? primaryTextStyles.withSecondaryText : primaryTextStyles.withoutSecondaryText, state.primaryText.className);
    }
    if (state.secondaryText) {
        state.secondaryText.className = (0, _react.mergeClasses)(interactionTagPrimaryClassNames.secondaryText, secondaryTextBaseClassName, state.secondaryText.className);
    }
    return state;
};
