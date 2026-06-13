<?php
// H4CK3D BY r00tk1t — LulzSec style defacement page
header('HTTP/1.1 200 OK');
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>H4CK3D BY r00tk1t</title>
<style>
body {
  background: #000;
  color: #0f0;
  font-family: 'Courier New', monospace;
  margin: 0;
  padding: 40px;
  text-align: center;
}
pre {
  font-size: 12px;
  line-height: 1.15;
  margin: 10px auto;
  display: inline-block;
  text-align: left;
}
img.logo {
  display: block;
  margin: 0 auto 10px auto;
  max-width: 400px;
  width: 90%;
  height: auto;
}
h1 {
  font-size: 42px;
  letter-spacing: 6px;
  text-shadow: 0 0 15px #0f0;
  margin: 25px 0 10px 0;
}
h2 {
  font-size: 22px;
  font-weight: normal;
  margin: 15px 0;
  color: #0c0;
}
.defacer {
  font-size: 20px;
  border-top: 1px solid #0f0;
  border-bottom: 1px solid #0f0;
  padding: 12px 0;
  margin: 20px auto;
  display: inline-block;
  color: #f00;
}
.gr33tz {
  font-size: 15px;
  line-height: 2;
  margin: 20px 0;
  color: #090;
}
.gr33tz b { color: #0f0; }
.footer {
  margin-top: 30px;
  font-size: 12px;
  color: #060;
  border-top: 1px dashed #060;
  padding-top: 15px;
}
</style>
</head>
<body>

<img class="logo" src="https://i.pinimg.com/736x/62/e1/eb/62e1eb51e8c4518a6a1e2cd34e469039.jpg" alt="Lulz Security">

<pre>
██████╗  ██████╗  ██████╗ ████████╗██╗  ██╗ ██╗████████╗
██╔══██╗██╔═████╗██╔═████╗╚══██╔══╝██║ ██╔╝██║╚══██╔══╝
██████╔╝██║██╔██║██║██╔██║   ██║   █████╔╝ ██║   ██║
██╔══██╗████╔╝██║████╔╝██║   ██║   ██╔═██╗ ██║   ██║
██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║  ██╗██║   ██║
╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝   ╚═╝
</pre>

<h1>// OWN3D //</h1>

<pre>
  .---.  .---.  .---.  .---.  .---.  .---.  .---.
  | L |  | U |  | L |  | Z |  | S |  | E |  | C |
  '---'  '---'  '---'  '---'  '---'  '---'  '---'
</pre>

<h2>✖ SYSTEM COMPROMISED ✖</h2>

<div class="defacer">
  D3F4C3D BY: r00tk1t
</div>

<div class="gr33tz">
  [ GR33TZ FR0M r00tk1t ]<br><br>
  <b>LulzSec</b> &mdash; for the lulz, for the pwnage<br>
</div>

<pre style="color:#060; margin-top:25px;">
"For the lulz. Always for the lulz."
</pre>

<div class="footer">
  [ H4CK3D @ r00tk1t ]
</div>

</body>
</html>
<?php
// Log the defacement view (optional)
$log = "[" . date('Y-m-d H:i:s') . "] " . $_SERVER['REMOTE_ADDR'] . " - " . $_SERVER['HTTP_USER_AGENT'] . "\n";
file_put_contents('/tmp/.deface_log.txt', $log, FILE_APPEND | LOCK_EX);
?>
