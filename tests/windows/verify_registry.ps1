# Verification Script for UKG Windows Registry
# Ensures Phase 41 registry logic is sound

Describe "UKG Registry Registration" {
    $RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine"

    Context "Installation Phase" {
        It "Registry path should exist after installation" {
            # Note: In a real test we'd run the installer, here we simulate/verify the logic
            $RegPath | Should Exist
        }

        It "Should have correct DisplayName" {
            (Get-ItemProperty $RegPath).DisplayName | Should Be "DataLogicEngine Desktop"
        }

        It "Should have UninstallString pointing to powershell" {
            (Get-ItemProperty $RegPath).UninstallString | Should Match "powershell.exe"
        }
    }
}
