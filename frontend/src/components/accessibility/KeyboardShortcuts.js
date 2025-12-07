import React, { useEffect, useCallback } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useDisclosure,
  Kbd,
  Text,
  VStack,
  Box
} from '@chakra-ui/react';
import { FocusTrap } from './FocusTrap';

/**
 * Keyboard Shortcuts Hook
 * Manages keyboard shortcuts for the application
 *
 * @param {Object} shortcuts - Map of key combinations to handlers
 * @param {boolean} enabled - Whether shortcuts are enabled
 */
export function useKeyboardShortcuts(shortcuts, enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event) => {
      const key = event.key.toLowerCase();
      const ctrl = event.ctrlKey || event.metaKey;
      const shift = event.shiftKey;
      const alt = event.altKey;

      // Build key combination string
      let combination = '';
      if (ctrl) combination += 'ctrl+';
      if (shift) combination += 'shift+';
      if (alt) combination += 'alt+';
      combination += key;

      // Check if combination matches any shortcut
      const handler = shortcuts[combination];
      if (handler) {
        event.preventDefault();
        handler(event);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, enabled]);
}

/**
 * Keyboard Shortcuts Help Modal
 * Displays available keyboard shortcuts to users
 * Opens with '?' or 'Shift+/' (WCAG 2.2 Level AAA - Help)
 */
export function KeyboardShortcutsHelp({ shortcuts = [] }) {
  const { isOpen, onOpen, onClose } = useDisclosure();

  const defaultShortcuts = [
    { keys: ['?', 'Shift+/'], description: 'Show keyboard shortcuts' },
    { keys: ['Esc'], description: 'Close dialog or cancel action' },
    { keys: ['Tab'], description: 'Move to next focusable element' },
    { keys: ['Shift+Tab'], description: 'Move to previous focusable element' },
    { keys: ['Enter'], description: 'Activate focused element' },
    { keys: ['Space'], description: 'Activate button or checkbox' },
    { keys: ['Arrow keys'], description: 'Navigate within components' },
    ...shortcuts
  ];

  // Listen for '?' key to open help
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        onOpen();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [onOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="xl"
      scrollBehavior="inside"
    >
      <ModalOverlay />
      <ModalContent>
        <FocusTrap active={isOpen} onEscape={onClose}>
          <ModalHeader>
            Keyboard Shortcuts
          </ModalHeader>
          <ModalCloseButton aria-label="Close keyboard shortcuts dialog" />
          <ModalBody pb={6}>
            <VStack align="stretch" spacing={4}>
              <Text color="gray.600">
                Use these keyboard shortcuts to navigate the application efficiently.
              </Text>

              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Shortcut</Th>
                    <Th>Description</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {defaultShortcuts.map((shortcut, index) => (
                    <Tr key={index}>
                      <Td>
                        <Box display="flex" gap={2}>
                          {Array.isArray(shortcut.keys) ? (
                            shortcut.keys.map((key, i) => (
                              <React.Fragment key={i}>
                                <Kbd>{key}</Kbd>
                                {i < shortcut.keys.length - 1 && <Text>or</Text>}
                              </React.Fragment>
                            ))
                          ) : (
                            <Kbd>{shortcut.keys}</Kbd>
                          )}
                        </Box>
                      </Td>
                      <Td>{shortcut.description}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>

              <Text fontSize="sm" color="gray.500" mt={4}>
                Press <Kbd>Esc</Kbd> to close this dialog
              </Text>
            </VStack>
          </ModalBody>
        </FocusTrap>
      </ModalContent>
    </Modal>
  );
}

export default useKeyboardShortcuts;
