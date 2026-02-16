# Pester tests for DataLogicEngine Windows Installer Scripts (Pester 3.4.0 Compatible)

Describe "UKG Windows Installer Scripts" {
    
    Context "Installer Logic" {
        It "Should require Administrator privileges" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\install.ps1" -Raw
            $Content | Should Match "Administrator"
        }

        It "Should have Strict Mode enabled" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\install.ps1" -Raw
            $Content | Should Match "Set-StrictMode"
        }

        It "Should have ErrorActionPreference set to Stop" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\install.ps1" -Raw
            # Using simpler match to avoid regex escape issues in Pester 3.4.0
            $Content | Should Match "ErrorActionPreference = .Stop."
        }

        It "Should support silent install mode" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\install.ps1" -Raw
            $Content | Should Match "Silent"
        }
    }

    Context "Hash Verification" {
        It "Should define a Test-UKGFileHash function" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\install.ps1" -Raw
            $Content | Should Match "function Test-UKGFileHash"
        }
    }

    Context "Retention Controls" {
        It "Uninstall script should support keep/delete data switches" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\uninstall.ps1" -Raw
            $Content | Should Match "KeepData"
            $Content | Should Match "DeleteData"
            $Content | Should Match "Silent"
        }
    }

    Context "Port Conflict Controls" {
        It "Startup script should expose auto-resolve port conflict option" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\start_local_stack.ps1" -Raw
            $Content | Should Match "AutoResolvePortConflicts"
            $Content | Should Match "Resolve-RequestedPort"
        }
    }

    Context "Dependency Scripts" {
        It "setup_db.ps1 should have try/catch blocks" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\setup_db.ps1" -Raw
            $Content | Should Match "try \{"
            $Content | Should Match "catch \{"
        }

        It "setup_cache.ps1 should have try/catch blocks" {
            $Content = Get-Content "$PSScriptRoot\..\..\scripts\windows\setup_cache.ps1" -Raw
            $Content | Should Match "try \{"
            $Content | Should Match "catch \{"
        }
    }
}
