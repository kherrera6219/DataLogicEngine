import '../styles/globals.css';
import '../styles/timeline.css';
import '../styles/app.css';
import { FluentProvider, SSRProvider, createDarkTheme } from '@fluentui/react-components';

const brandRamp = {
  10: '#02040a',
  20: '#061328',
  30: '#0a1f3d',
  40: '#0c2a52',
  50: '#0e3567',
  60: '#0f417b',
  70: '#144c90',
  80: '#1c5aa3',
  90: '#2768b7',
  100: '#3274c6',
  110: '#3c81d4',
  120: '#468ee0',
  130: '#5a9bec',
  140: '#75acf2',
  150: '#9cc2f7',
  160: '#c7dcfb',
};

const enterpriseDarkTheme = {
  ...createDarkTheme(brandRamp),
  colorNeutralBackground1: '#0d1117',
  colorNeutralBackground2: '#111723',
  colorNeutralBackground3: '#162133',
  colorNeutralBackground4: '#19263b',
  colorNeutralBackground6: '#0f1622',
  colorNeutralForeground1: '#f3f6fb',
  colorNeutralForeground2: '#d0d7e3',
  colorNeutralForeground3: '#a0aec0',
  colorNeutralForegroundOnBrand: '#ffffff',
  colorNeutralStroke1: '#2b3648',
  colorBrandForegroundLink: '#75acf2',
  colorBrandForegroundLinkHover: '#9cc2f7',
  colorBrandForegroundLinkPressed: '#9cc2f7',
  colorBrandBackground: brandRamp[80],
  colorBrandBackgroundHover: brandRamp[70],
  colorBrandBackgroundPressed: brandRamp[60],
};

function MyApp({ Component, pageProps }) {
  return (
    <SSRProvider>
      <FluentProvider theme={enterpriseDarkTheme} style={{ minHeight: '100vh' }}>
        <Component {...pageProps} />
      </FluentProvider>
    </SSRProvider>
  );
}

export default MyApp;
