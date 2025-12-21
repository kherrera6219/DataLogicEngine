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
    interactionTagSecondaryClassNames: function() {
        return interactionTagSecondaryClassNames;
    },
    useInteractionTagSecondaryStyles_unstable: function() {
        return useInteractionTagSecondaryStyles_unstable;
    }
});
const _react = require("@griffel/react");
const interactionTagSecondaryClassNames = {
    root: 'fui-InteractionTagSecondary'
};
const mediumIconSize = '20px';
const smallIconSize = '16px';
const extraSmallIconSize = '12px';
const useRootBaseClassName = /*#__PURE__*/ (0, _react.__resetStyles)("rxqbxwz", "rdjx360", [
    ".rxqbxwz{color:inherit;font-family:inherit;padding:0px;border-style:none;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;background-color:transparent;display:flex;height:100%;align-items:center;border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-left-color:var(--colorNeutralStroke1);border-top-left-radius:var(--borderRadiusNone);border-bottom-left-radius:var(--borderRadiusNone);}",
    ".rxqbxwz[data-fui-focus-visible]{outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);}",
    ".rdjx360{color:inherit;font-family:inherit;padding:0px;border-style:none;-webkit-appearance:button;-moz-appearance:button;appearance:button;text-align:unset;background-color:transparent;display:flex;height:100%;align-items:center;border:var(--strokeWidthThin) solid var(--colorTransparentStroke);border-right-color:var(--colorNeutralStroke1);border-top-right-radius:var(--borderRadiusNone);border-bottom-right-radius:var(--borderRadiusNone);}",
    ".rdjx360[data-fui-focus-visible]{outline:var(--strokeWidthThick) solid var(--colorStrokeFocus2);}"
]);
const useRootStyles = /*#__PURE__*/ (0, _react.__styles)({
    filled: {
        De3pzq: "f16xq7d1",
        sj55zd: "fkfq4zb",
        B4j52fo: "fre7gi1",
        Bn0qgzm: "fqdk4by",
        eoavqd: "f8491dx",
        Jwef8y: "f1h648pw",
        Bi91k9c: "f139oj5f",
        ecr2s2: "fwdzr64",
        lj723h: "f19au66r",
        kr9cjb: "fmvl6o9",
        u9orzk: "fb8cdra",
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
        Bi91k9c: "f139oj5f",
        ecr2s2: "f1wfn5kd",
        lj723h: "f19au66r",
        Bbkh6qg: "fkiggi6",
        Cnge2b: "f8zknr1"
    },
    brand: {
        De3pzq: "f16xkysk",
        sj55zd: "faj9fo0",
        zhjwy3: [
            "f1sl6hi9",
            "f1c8dzaj"
        ],
        B4j52fo: "fre7gi1",
        Bn0qgzm: "fqdk4by",
        eoavqd: "f8491dx",
        Jwef8y: "f1yj72w4",
        Bi91k9c: "f3ymbdj",
        ecr2s2: "fy3sl2y",
        lj723h: "fryz5bw",
        kr9cjb: "fmvl6o9",
        u9orzk: "fb8cdra",
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
            "f4j9k2g",
            "f1mg2euo"
        ],
        B8gzw0y: "f1h3a8gf",
        By8wz76: "f1nz3ub2",
        B7iucu3: "fqc85l4",
        Jwef8y: "f15wkkf3",
        Bi91k9c: "f1rq72xc",
        Bbkh6qg: "f1tx4pjd",
        Bahaeuw: "fu37p9p",
        ecr2s2: "fsp1bjw",
        lj723h: "f18otbis",
        Cnge2b: "f16z8z4r",
        Boo3t63: "f7ydw7o"
    },
    rounded: {
        B7oj6ja: [
            "f1jar5jt",
            "fyu767a"
        ],
        Bbmb7ep: [
            "f1aa9q02",
            "f16jpd5f"
        ]
    },
    circular: {
        B7oj6ja: [
            "f1djnp8u",
            "f1s8kh49"
        ],
        Bbmb7ep: [
            "f8fbkgy",
            "f1nfllo7"
        ]
    },
    medium: {
        Be2twd7: "fe5j1ua",
        uwmqm3: [
            "f15vdbe4",
            "fwiuce9"
        ],
        z189sj: [
            "fwiuce9",
            "f15vdbe4"
        ]
    },
    small: {
        Be2twd7: "f4ybsrx",
        uwmqm3: [
            "f2lugmd",
            "f6zblan"
        ],
        z189sj: [
            "f6zblan",
            "f2lugmd"
        ]
    },
    "extra-small": {
        Be2twd7: "f1ugzwwg",
        uwmqm3: [
            "f15vdbe4",
            "fwiuce9"
        ],
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
        ".fre7gi1{border-top-width:0;}",
        ".fqdk4by{border-bottom-width:0;}",
        ".fhovq9v{background-color:var(--colorSubtleBackground);}",
        ".fj3muxo{border-top-color:var(--colorNeutralStroke1);}",
        ".f1akhkt{border-right-color:var(--colorNeutralStroke1);}",
        ".f1lxtadh{border-left-color:var(--colorNeutralStroke1);}",
        ".f1aperda{border-bottom-color:var(--colorNeutralStroke1);}",
        ".f16xkysk{background-color:var(--colorBrandBackground2);}",
        ".faj9fo0{color:var(--colorBrandForeground2);}",
        ".f1sl6hi9{border-left-color:var(--colorBrandStroke2);}",
        ".f1c8dzaj{border-right-color:var(--colorBrandStroke2);}",
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
        ".f4j9k2g{border-left-color:var(--colorNeutralStrokeOnBrand2);}",
        ".f1mg2euo{border-right-color:var(--colorNeutralStrokeOnBrand2);}",
        ".f1jar5jt{border-top-right-radius:var(--borderRadiusMedium);}",
        ".fyu767a{border-top-left-radius:var(--borderRadiusMedium);}",
        ".f1aa9q02{border-bottom-right-radius:var(--borderRadiusMedium);}",
        ".f16jpd5f{border-bottom-left-radius:var(--borderRadiusMedium);}",
        ".f1djnp8u{border-top-right-radius:var(--borderRadiusCircular);}",
        ".f1s8kh49{border-top-left-radius:var(--borderRadiusCircular);}",
        ".f8fbkgy{border-bottom-right-radius:var(--borderRadiusCircular);}",
        ".f1nfllo7{border-bottom-left-radius:var(--borderRadiusCircular);}",
        ".fe5j1ua{font-size:20px;}",
        ".f15vdbe4{padding-left:5px;}",
        ".fwiuce9{padding-right:5px;}",
        ".f4ybsrx{font-size:16px;}",
        ".f2lugmd{padding-left:3px;}",
        ".f6zblan{padding-right:3px;}",
        ".f1ugzwwg{font-size:12px;}",
        ".f10pi13n{position:relative;}"
    ],
    h: [
        ".f8491dx:hover{cursor:pointer;}",
        ".f1h648pw:hover{background-color:var(--colorNeutralBackground3Hover);}",
        ".f139oj5f:hover{color:var(--colorNeutralForeground2BrandHover);}",
        ".f1t94bn6:hover{background-color:var(--colorSubtleBackgroundHover);}",
        ".f1yj72w4:hover{background-color:var(--colorBrandBackground2Hover);}",
        ".f3ymbdj:hover{color:var(--colorCompoundBrandForeground1Hover);}",
        ".f15wkkf3:hover{background-color:var(--colorBrandBackgroundHover);}",
        ".f1rq72xc:hover{color:var(--colorNeutralForegroundOnBrand);}"
    ],
    a: [
        ".fwdzr64:active{background-color:var(--colorNeutralBackground3Pressed);}",
        ".f19au66r:active{color:var(--colorNeutralForeground2BrandPressed);}",
        ".f1wfn5kd:active{background-color:var(--colorSubtleBackgroundPressed);}",
        ".fy3sl2y:active{background-color:var(--colorBrandBackground2Pressed);}",
        ".fryz5bw:active{color:var(--colorCompoundBrandForeground1Pressed);}",
        ".fsp1bjw:active{background-color:var(--colorBrandBackgroundPressed);}",
        ".f18otbis:active{color:var(--colorNeutralForegroundOnBrand);}"
    ],
    m: [
        [
            "@media (forced-colors: active){.fmvl6o9{border-top-width:var(--strokeWidthThin);}}",
            {
                m: "(forced-colors: active)"
            }
        ],
        [
            "@media (forced-colors: active){.fb8cdra{border-bottom-width:var(--strokeWidthThin);}}",
            {
                m: "(forced-colors: active)"
            }
        ],
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
const useRootDisabledStyles = /*#__PURE__*/ (0, _react.__styles)({
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
            "fy0fskl",
            "f15xbau"
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
            "fy0fskl",
            "f15xbau"
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
        ".fy0fskl{border-left-color:var(--colorNeutralStrokeDisabled);}",
        ".f15xbau{border-right-color:var(--colorNeutralStrokeDisabled);}",
        ".fhovq9v{background-color:var(--colorSubtleBackground);}",
        ".f1jj8ep1{border-top-color:var(--colorNeutralStrokeDisabled);}",
        ".f4ikngz{border-bottom-color:var(--colorNeutralStrokeDisabled);}"
    ]
});
const useInteractionTagSecondaryStyles_unstable = (state)=>{
    'use no memo';
    const rootBaseClassName = useRootBaseClassName();
    const rootStyles = useRootStyles();
    const rootDisabledStyles = useRootDisabledStyles();
    const { disabled, selected, shape, size, appearance } = state;
    state.root.className = (0, _react.mergeClasses)(interactionTagSecondaryClassNames.root, rootBaseClassName, disabled ? rootDisabledStyles[appearance] : rootStyles[appearance], rootStyles[shape], rootStyles[size], selected && !disabled && rootStyles.selected, state.root.className);
    return state;
};
