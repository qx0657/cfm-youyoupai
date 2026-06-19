import { existsSync, mkdirSync, readFileSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const envPath = path.join(projectRoot, ".env.deploy");

function parseEnvFile(filePath) {
  if (!existsSync(filePath)) return {};
  const result = {};
  const lines = readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (!match) continue;
    const [, key, rawValue] = match;
    result[key] = rawValue.replace(/^["']|["']$/g, "");
  }
  return result;
}

function run(command, args, options = {}) {
  console.log(`\n$ ${[command, ...args].join(" ")}`);
  const result = spawnSync(command, args, {
    cwd: options.cwd || projectRoot,
    env: { ...process.env, ...options.env },
    shell: false,
    stdio: "inherit",
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`${command} failed with exit code ${result.status}`);
  }
}

function runNpm(args) {
  if (process.platform === "win32") {
    run("cmd.exe", ["/d", "/s", "/c", `npm.cmd ${args.join(" ")}`]);
    return;
  }
  run("npm", args);
}

function requireConfig(config, key) {
  const value = config[key];
  if (!value) {
    throw new Error(`Missing ${key}. Please copy .env.deploy.example to .env.deploy and fill it.`);
  }
  return value;
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, "'\\''")}'`;
}

const config = {
  ...parseEnvFile(envPath),
  ...process.env,
};

const host = requireConfig(config, "DEPLOY_HOST");
const user = requireConfig(config, "DEPLOY_USER");
const remoteDir = requireConfig(config, "DEPLOY_REMOTE_DIR");
const port = config.DEPLOY_PORT || "22";
const sshKey = config.DEPLOY_SSH_KEY;
const remote = `${user}@${host}`;
const distDir = path.join(projectRoot, "dist");
const deployDir = path.join(projectRoot, ".deploy");
const archiveName = `cfuu-app-${Date.now()}.tar.gz`;
const archivePath = path.join(deployDir, archiveName);
const remoteArchive = `/tmp/${archiveName}`;
const archiveEntries = [
  "admin",
  "data",
  "dist",
  "public",
  "scripts",
  "src",
  "index.html",
  "package.json",
  "package-lock.json",
  "tsconfig.json",
  "vite.config.ts",
  "PIPELINE.md",
  "VIDEO_INTEGRATION.md",
];

const sshArgs = ["-p", port];
if (sshKey) sshArgs.push("-i", sshKey);
if (config.DEPLOY_SSH_EXTRA_ARGS) {
  sshArgs.push(...config.DEPLOY_SSH_EXTRA_ARGS.split(/\s+/).filter(Boolean));
}

const scpArgs = ["-P", port];
if (sshKey) scpArgs.push("-i", sshKey);
if (config.DEPLOY_SSH_EXTRA_ARGS) {
  scpArgs.push(...config.DEPLOY_SSH_EXTRA_ARGS.split(/\s+/).filter(Boolean));
}

try {
  mkdirSync(deployDir, { recursive: true });
  rmSync(archivePath, { force: true });

  runNpm(["run", "prepare:data"]);
  runNpm(["run", "build"]);

  if (!existsSync(distDir)) {
    throw new Error("dist directory was not generated.");
  }

  run("tar", ["-czf", archivePath, "-C", projectRoot, ...archiveEntries.filter((entry) => existsSync(path.join(projectRoot, entry)))]);
  run("scp", [...scpArgs, archivePath, `${remote}:${remoteArchive}`]);

  const remoteCommand = [
    `mkdir -p ${shellQuote(remoteDir)}`,
    `tar -xzf ${shellQuote(remoteArchive)} -C ${shellQuote(remoteDir)}`,
    `rm -f ${shellQuote(remoteArchive)}`,
    `chown -R www:www ${shellQuote(remoteDir)} || true`,
  ].join(" && ");
  run("ssh", [...sshArgs, remote, remoteCommand]);

  console.log(`\nDeploy complete: ${remote}:${remoteDir}`);
} finally {
  if (config.DEPLOY_KEEP_ARCHIVE !== "1") {
    rmSync(archivePath, { force: true });
    if (existsSync(deployDir) && os.platform() !== "win32") {
      rmSync(deployDir, { recursive: true, force: true });
    }
  }
}
