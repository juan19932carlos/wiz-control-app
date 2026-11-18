import { usePluginData } from '@docusaurus/useGlobalData';
import QRCode from 'qrcode';
import { useEffect, useMemo, useState, type ReactNode } from 'react';

/** Placeholders in compose.prod.yaml. The plugin in docusaurus.config.ts fails the build if they disappear. */
export const TARGETS_PLACEHOLDER = /\$\{WIZ_TARGETS:\?[^}]*\}/;
export const PORT_PLACEHOLDER = /\$\{WEB_PORT:-\d+\}/;

const IPV4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;

type Parsed = { ok: true; octets: number[]; port: number } | { ok: false; error: string };

function parse(ip: string, port: string): Parsed {
  const match = IPV4.exec(ip.trim());
  if (!match) return { ok: false, error: 'Write the IPv4 address exactly as ipconfig shows it, like 192.168.1.23.' };
  const octets = match.slice(1).map(Number);
  if (octets.some((n) => n > 255)) return { ok: false, error: 'Each number in the address must be between 0 and 255.' };
  const portNumber = Number(port);
  if (!Number.isInteger(portNumber) || portNumber < 1 || portNumber > 65535) {
    return { ok: false, error: 'The port must be a whole number between 1 and 65535. If unsure, use 8080.' };
  }
  return { ok: true, octets, port: portNumber };
}

/** Home routers almost always use a /24 network: the first three numbers are shared by every device. */
function isPrivate([a, b]: number[]): boolean {
  return a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
}

function download(text: string, filename: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/yaml' }));
  const link = Object.assign(document.createElement('a'), { href: url, download: filename });
  link.click();
  URL.revokeObjectURL(url);
}

export default function ComposeGenerator(): ReactNode {
  const { compose } = usePluginData('compose-file') as { compose: string };
  const [ip, setIp] = useState('');
  const [port, setPort] = useState('8080');
  const [qr, setQr] = useState<string | null>(null);

  const parsed = useMemo(() => parse(ip, port), [ip, port]);
  const url = parsed.ok ? `http://${parsed.octets.join('.')}:${parsed.port}` : null;
  const subnet = parsed.ok ? `${parsed.octets.slice(0, 3).join('.')}.0/24` : null;

  useEffect(() => {
    if (!url) return setQr(null);
    QRCode.toDataURL(url, { margin: 1, width: 220 }).then(setQr, () => setQr(null));
  }, [url]);

  const file =
    parsed.ok && subnet
      ? compose.replace(TARGETS_PLACEHOLDER, subnet).replace(PORT_PLACEHOLDER, String(parsed.port))
      : null;

  return (
    <div className="card shadow--md margin-vert--lg">
      <div className="card__body">
        <div className="row">
          <div className="col col--6 margin-bottom--md">
            <label htmlFor="wiz-ip"><b>Your computer's IPv4 address</b></label>
            <input
              id="wiz-ip"
              className="wiz-input"
              inputMode="decimal"
              autoComplete="off"
              placeholder="192.168.1.23"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
            />
          </div>
          <div className="col col--6 margin-bottom--md">
            <label htmlFor="wiz-port"><b>Port</b> (leave 8080 if unsure)</label>
            <input
              id="wiz-port"
              className="wiz-input"
              inputMode="numeric"
              value={port}
              onChange={(e) => setPort(e.target.value)}
            />
          </div>
        </div>

        {ip.trim() === '' ? null : !parsed.ok ? (
          <div className="alert alert--warning">{parsed.error}</div>
        ) : (
          <>
            {!isPrivate(parsed.octets) && (
              <div className="alert alert--warning margin-bottom--md">
                This does not look like a home network address. Home addresses usually start with 192.168, 10, or
                172. Check that you copied the <b>IPv4 Address</b> line of your Wi-Fi or Ethernet adapter.
              </div>
            )}
            <div className="row">
              <div className="col col--8">
                <p>
                  Your app will be at:
                  <br />
                  <code className="wiz-url">{url}</code>
                </p>
                <p>
                  The app will look for bulbs on the network <code>{subnet}</code>.
                </p>
                <button className="button button--primary button--lg" onClick={() => file && download(file, 'compose.yaml')}>
                  Download compose.yaml
                </button>
              </div>
              <div className="col col--4 text--center">
                {qr && <img src={qr} alt={`QR code for ${url}`} width={180} height={180} />}
                <div><small>Scan with your phone camera</small></div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
