import type { Meta, StoryObj } from '@storybook/react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';

const meta: Meta<typeof Sheet> = {
  title: 'Fluent UI/Primitives/Sheet',
  component: Sheet,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof Sheet>;

export const Default: Story = {
  render: () => (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline">Open Sheet</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Sheet Title</SheetTitle>
        </SheetHeader>
        <div className="py-4">
            <p>Sheet content goes here...</p>
        </div>
      </SheetContent>
    </Sheet>
  ),
};
