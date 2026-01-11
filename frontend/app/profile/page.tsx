'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

export default function ProfilePage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-5xl">
         <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">User Profile</h1>
            <p className="text-gray-500">Manage your personal information and security settings.</p>
         </header>

         <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* User Info Card */}
            <Card className="lg:col-span-1">
               <CardHeader className="flex flex-col items-center text-center">
                  <Avatar className="w-32 h-32 mb-4">
                     {/* Placeholder for real image */}
                     <AvatarFallback className="text-4xl bg-blue-100 text-blue-600">JD</AvatarFallback>
                  </Avatar>
                  <CardTitle className="text-xl">John Doe</CardTitle>
                  <CardDescription>Senior Knowledge Engineer</CardDescription>
                  <div className="mt-2">
                     <Badge variant="success">Admin</Badge>
                  </div>
               </CardHeader>
               <CardContent className="space-y-4">
                  <div className="border-t pt-4">
                     <div className="text-sm font-medium text-gray-500">Email</div>
                     <div className="text-gray-900 dark:text-gray-200">john.doe@example.com</div>
                  </div>
                  <div>
                     <div className="text-sm font-medium text-gray-500">Department</div>
                     <div className="text-gray-900 dark:text-gray-200">System Operations</div>
                  </div>
                  <div>
                     <div className="text-sm font-medium text-gray-500">Joined</div>
                     <div className="text-gray-900 dark:text-gray-200">Jan 10, 2024</div>
                  </div>
               </CardContent>
            </Card>

            {/* Edit Profile Form */}
            <Card className="lg:col-span-2">
               <CardHeader>
                  <CardTitle>Edit Profile</CardTitle>
                  <CardDescription>Update your account details.</CardDescription>
               </CardHeader>
               <CardContent>
                  <form className="space-y-6">
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                           <label className="text-sm font-medium">First Name</label>
                           <Input defaultValue="John" />
                        </div>
                        <div className="space-y-2">
                           <label className="text-sm font-medium">Last Name</label>
                           <Input defaultValue="Doe" />
                        </div>
                     </div>
                     
                     <div className="space-y-2">
                        <label className="text-sm font-medium">Email Address</label>
                        <Input defaultValue="john.doe@example.com" type="email" />
                     </div>
                     
                     <div className="space-y-2">
                        <label className="text-sm font-medium">Job Title</label>
                        <Input defaultValue="Senior Knowledge Engineer" />
                     </div>

                     <div className="pt-4 flex justify-end gap-2">
                        <Button variant="outline">Cancel</Button>
                        <Button>Save Changes</Button>
                     </div>
                  </form>
               </CardContent>
            </Card>
         </div>
      </div>
    </main>
  );
}
