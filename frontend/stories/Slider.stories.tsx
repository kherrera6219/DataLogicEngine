import type { Meta, StoryObj } from '@storybook/react';
import { Slider } from "@/components/ui/slider"

const meta: Meta<typeof Slider> = {
  title: 'Fluent UI/Primitives/Slider',
  component: Slider,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof Slider>;

export const Default: Story = {
    args: {
        defaultValue: [50],
        max: 100,
        step: 1,
        className: "w-[60%]"
    }
};
