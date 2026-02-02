import type { Meta, StoryObj } from '@storybook/react';
import { AxisSelector } from '@/components/Graph/AxisSelector';
import { useState } from 'react';

const meta: Meta<typeof AxisSelector> = {
  title: 'Graph/AxisSelector',
  component: AxisSelector,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof AxisSelector>;

export const Default: Story = {
    render: () => {
        const [active, setActive] = useState(1);
        return <AxisSelector activeAxis={active} onChange={setActive} />;
    }
};
