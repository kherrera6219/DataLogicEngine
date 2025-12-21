import type { Serialized } from 'extension/types';
import type { References } from 'extension/utils/references';
export declare const serialize: <Data extends object>(data: Data, references: References) => Serialized<Data>;
