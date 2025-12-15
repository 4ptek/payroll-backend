module.exports = {
  apps: [
    {
      name: "hrms",
      script: "manage.py",
      args: "runserver 127.0.0.1:8000",
      interpreter: "python",
      watch: false,       // Django reload already handles changes
      autorestart: true,
      max_memory_restart: "500M",
      env: {
        DJANGO_SETTINGS_MODULE: "hrms.settings",
      }
    }
  ]
};
