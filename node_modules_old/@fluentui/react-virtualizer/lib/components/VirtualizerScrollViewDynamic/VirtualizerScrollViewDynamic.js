'use client';
import { useVirtualizerScrollViewDynamic_unstable } from './useVirtualizerScrollViewDynamic';
import { renderVirtualizerScrollViewDynamic_unstable } from './renderVirtualizerScrollViewDynamic';
import { useVirtualizerScrollViewDynamicStyles_unstable } from './useVirtualizerScrollViewDynamicStyles.styles';
import * as React from 'react';
import { useCustomStyleHook_unstable } from '@fluentui/react-shared-contexts';
/**
 * Virtualizer ScrollView
 * @deprecated migrated to \@fluentui\-contrib/react\-virtualizer for stable release.
 */ export const VirtualizerScrollViewDynamic = (props, // NOTE: this second context parameter doesn't exists in React 19
_context)=>{
    const state = useVirtualizerScrollViewDynamic_unstable(props);
    useVirtualizerScrollViewDynamicStyles_unstable(state);
    useCustomStyleHook_unstable('useVirtualizerScrollViewDynamicStyles_unstable')(state);
    return renderVirtualizerScrollViewDynamic_unstable(state);
// NOTE: we need to assert the type to satisfy tsc (React 19 FC doesn't have 2nd context parameter anymore)
};
VirtualizerScrollViewDynamic.displayName = 'VirtualizerScrollViewDynamic';
