# Robopro
## ROBOPRO — управляющее приложение для промышленного манипулятора: RobotController + OPC UA сервер + GUI. Поддерживает очереди команд, watchdog и автозапуск через systemd.
- Rc - robot controller
- opc - opc handler
- mb - moodbus

### robopro.service path - /home/user/.config/systemd/user
## Activating:
- systemctl --user daemon-reload
- systemctl --user enable --now robopro.service
- systemctl --user status robopro.service -l
- journalctl --user -u robopro.service -f -o cat
