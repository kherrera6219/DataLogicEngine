using System;
using System.Diagnostics;
using System.IO;
using System.ComponentModel;

class UKGWrapper
{
    static void Main(string[] args)
    {
        // Detect if we are Setup or Uninstall based on filename
        string exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
        string exeName = Path.GetFileNameWithoutExtension(exePath).ToLower();
        
        string scriptFile = exeName.Contains("setup") ? "install.ps1" : "uninstall.ps1";
        string scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "scripts", "windows", scriptFile);

        if (!File.Exists(scriptPath))
        {
            Console.WriteLine("Error: Required script not found at: " + scriptPath);
            Console.WriteLine("Please ensure the 'scripts' directory is present in the application root.");
            Console.WriteLine("\nPress Enter to exit...");
            Console.ReadLine();
            return;
        }

        Console.WriteLine("--- DataLogicEngine Bootstrap Loader ---");
        Console.WriteLine("Launching: " + scriptFile);
        Console.WriteLine("\n** A Windows security prompt will appear. Please click 'Yes' to continue. **\n");

        ProcessStartInfo startInfo = new ProcessStartInfo();
        startInfo.FileName = "powershell.exe";
        startInfo.Arguments = "-ExecutionPolicy Bypass -File \"" + scriptPath + "\"";
        startInfo.UseShellExecute = true;
        startInfo.Verb = "runas"; // Request Elevation

        try
        {
            Process process = Process.Start(startInfo);
            process.WaitForExit();
            Console.WriteLine("\nInstallation process completed. Exit code: " + process.ExitCode);
        }
        catch (Win32Exception ex)
        {
            if (ex.NativeErrorCode == 1223)
            {
                // ERROR_CANCELLED - User clicked "No" on UAC
                Console.WriteLine("\n*** Installation cancelled by user. ***");
                Console.WriteLine("Administrator privileges are required to install DataLogicEngine.");
            }
            else
            {
                Console.WriteLine("Failed to launch process: " + ex.Message);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("Failed to launch process: " + ex.Message);
        }

        Console.WriteLine("\nPress Enter to exit...");
        Console.ReadLine();
    }
}
