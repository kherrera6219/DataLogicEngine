"use client";
'use strict';

var React = require('react');

function _interopNamespaceCompat(e) {
  if (e && typeof e === 'object' && 'default' in e) return e;
  var n = Object.create(null);
  if (e) {
    Object.keys(e).forEach(function (k) {
      if (k !== 'default') {
        var d = Object.getOwnPropertyDescriptor(e, k);
        Object.defineProperty(n, k, d.get ? d : {
          enumerable: true,
          get: function () { return e[k]; }
        });
      }
    });
  }
  n.default = e;
  return Object.freeze(n);
}

var React__namespace = /*#__PURE__*/_interopNamespaceCompat(React);

function getDispatcher() {
  try {
    return React__namespace[''.concat('__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE')].H;
  } catch (_unused) {
    // React 19+
  }
  try {
    return React__namespace[''.concat('__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED')].ReactCurrentDispatcher.current;
  } catch (_unused2) {
    // React 18 and below
  }
}
function isInsideComponent() {
  // React 18 always logs errors if a dispatcher is not present:
  // https://github.com/facebook/react/blob/42f15b324f50d0fd98322c21646ac3013e30344a/packages/react/src/ReactHooks.js#L26-L36
  try {
    const dispatcher = getDispatcher();
    // Before any React component was rendered "dispatcher" will be "null"
    if (dispatcher === null || dispatcher === undefined) {
      return false;
    }
    // A check with hooks call (i.e. call "React.useContext()" outside a component) will always produce errors, but
    // a call on the dispatcher wont
    dispatcher.useContext({});
    return true;
  } catch (e) {
    return false;
  }
}

exports.isInsideComponent = isInsideComponent;
//# sourceMappingURL=isInsideComponent.cjs.js.map
