import type { Meta, StoryObj } from '@storybook/react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useState } from 'react';

const meta = {
  title: 'Fluent UI/Primitives/Tabs',
  component: Tabs,
  tags: ['autodocs'],
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

const TabsDemo = () => {
  const [tab, setTab] = useState('account');
  return (
    <Tabs value={tab} onValueChange={setTab} className="w-[400px]">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="account">Account</TabsTrigger>
        <TabsTrigger value="password">Password</TabsTrigger>
      </TabsList>
      <TabsContent value="account">
        <div className="p-4 border rounded-md mt-2 bg-neutral-900 text-white">
          <h3 className="font-bold">Account</h3>
          <p className="text-gray-400 text-sm">Make changes to your account here.</p>
        </div>
      </TabsContent>
      <TabsContent value="password">
        <div className="p-4 border rounded-md mt-2 bg-neutral-900 text-white">
          <h3 className="font-bold">Password</h3>
          <p className="text-gray-400 text-sm">Change your password here.</p>
        </div>
      </TabsContent>
    </Tabs>
  );
};

export const Default: Story = {
  render: () => <TabsDemo />,
};
