import type { Meta, StoryObj } from '@storybook/react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const meta: Meta<typeof Dialog> = {
  title: 'Fluent UI/Primitives/Dialog',
  component: Dialog,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof Dialog>;

export const Default: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Open Dialog</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
        </DialogHeader>
        <div className="py-4">
             <p>Make changes to your profile here.</p>
        </div>
      </DialogContent>
    </Dialog>
  ),
};
