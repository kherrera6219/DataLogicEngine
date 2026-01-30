using System;
using System.Diagnostics;
using System.IO;

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
            Console.ReadLine();
            return;
        }

        Console.WriteLine("--- DataLogicEngine Bootstrap Loader ---");
        Console.WriteLine("Launching: " + scriptFile);

        ProcessStartInfo startInfo = new ProcessStartInfo();
        startInfo.FileName = "powershell.exe";
        startInfo.Arguments = "-ExecutionPolicy Bypass -File \"" + scriptPath + "\"";
        startInfo.UseShellExecute = true;
        startInfo.Verb = "runas"; // Request Elevation

        try
        {
            Process process = Process.Start(startInfo);
            process.WaitForExit();
        }
        catch (Exception ex)
        {
            Console.WriteLine("Failed to launch process: " + ex.Message);
            Console.ReadLine();
        }
    }
}
