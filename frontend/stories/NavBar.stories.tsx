import type { Meta, StoryObj } from '@storybook/react';
import { NavBar } from '@/components/NavBar';

// Mock useRouter/usePathname
// Note: In Next.js App Router, components often need decorators or mocks for navigation.
// This story might fail if it uses navigation hooks directly without context.
// Assuming it might need a decorator, but let's try basic render.

const meta: Meta<typeof NavBar> = {
  title: 'Layout/NavBar',
  component: NavBar,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof NavBar>;

export const Default: Story = {};
