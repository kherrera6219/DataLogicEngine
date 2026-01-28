import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ShieldCheck } from 'lucide-react';

const meta = {
  title: 'Fluent UI/Primitives/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultFluent: Story = {
  render: () => (
    <Card className="fluent-card w-[350px] bg-[#1a1a1a] border-[#333]">
      <CardHeader>
        <CardTitle>System Status</CardTitle>
        <CardDescription>Real-time metrics from the registry.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <ShieldCheck className="h-8 w-8 text-green-500" />
          <div>
            <div className="text-2xl font-bold">99.9%</div>
            <div className="text-xs text-gray-500">Uptime Score</div>
          </div>
        </div>
      </CardContent>
    </Card>
  ),
};

export const Interactive: Story = {
  render: () => (
    <Card className="fluent-card w-[350px] bg-[#1a1a1a] border-[#333] hover:border-blue-500/50 hover:-translate-y-1 transition-all cursor-pointer group">
       <CardContent className="p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500/10 to-transparent rounded-bl-full -mr-8 -mt-8 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <CardTitle className="mb-2">Interactive Card</CardTitle>
          <CardDescription>Hover over me to see the fluent reveal effect and elevation change.</CardDescription>
       </CardContent>
    </Card>
  ),
};
