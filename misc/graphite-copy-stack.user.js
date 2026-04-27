// ==UserScript==
// @name         Graphite: Copy Stack (Custom Format)
// @namespace    https://app.graphite.com
// @version      1.7
// @match        https://app.graphite.com/*
// @grant        GM_setClipboard
// @inject-into  content
// ==/UserScript==

(function () {
    'use strict';

    function transformHtml(html) {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const body = doc.body;
        const nodes = [...body.childNodes];

        // Group nodes into segments split by <br>
        const segments = [];
        let current = [];
        for (const node of nodes) {
            if (node.nodeName === 'BR') {
                segments.push(current);
                current = [];
            } else {
                current.push(node);
            }
        }
        if (current.length) segments.push(current);

        // Strip leading emoji text node from each segment
        for (const seg of segments) {
            const first = seg[0];
            if (first && first.nodeType === Node.TEXT_NODE) {
                first.textContent = first.textContent.replace(/^[\p{Emoji_Presentation}\p{Extended_Pictographic}\s]+/u, '');
            }
        }

        // Rebuild body in reverse order
        while (body.firstChild) body.removeChild(body.firstChild);
        segments.reverse().forEach((seg, i) => {
            seg.forEach(n => body.appendChild(n));
            if (i < segments.length - 1) body.appendChild(doc.createElement('br'));
        });

        return '<meta charset="utf-8">' + body.innerHTML;
    }

    function transformText(text) {
        return text
            .split('\n')
            .filter(l => l.trim())
            .map(line => line.replace(/^.*?(?=\[)/, '').trim())
            .reverse()
            .join('\n');
    }

    async function handleClick(e, originalBtn) {
        e.stopPropagation();
        originalBtn.click();
        await new Promise(r => setTimeout(r, 300));

        const items = await navigator.clipboard.read();
        let htmlBlob = null, textStr = null;

        for (const item of items) {
            if (item.types.includes('text/html')) htmlBlob = await item.getType('text/html');
            if (item.types.includes('text/plain')) textStr = await (await item.getType('text/plain')).text();
        }

        if (htmlBlob) {
            const transformedHtml = transformHtml(await htmlBlob.text());
            const transformedText = textStr ? transformText(textStr) : '';
            await navigator.clipboard.write([new ClipboardItem({
                'text/html': new Blob([transformedHtml], { type: 'text/html' }),
                'text/plain': new Blob([transformedText], { type: 'text/plain' }),
            })]);
        } else if (textStr) {
            GM_setClipboard(transformText(textStr));
        }

        this.textContent = 'Copied!';
        setTimeout(() => { this.textContent = 'Copy ↑'; }, 1500);
    }

    function inject(originalBtn) {
        if (originalBtn.dataset.gtCustom) return;
        originalBtn.dataset.gtCustom = '1';
        const btn = originalBtn.cloneNode(true);
        btn.textContent = 'Copy ↑';
        delete btn.dataset.gtCustom;
        btn.addEventListener('click', function (e) { handleClick.call(this, e, originalBtn); });
        originalBtn.after(btn);
    }

    new MutationObserver(() => {
        document.querySelectorAll('button').forEach(btn => {
            if (/copy.*stack/i.test(btn.textContent) && !btn.dataset.gtCustom) inject(btn);
        });
    }).observe(document.body, { childList: true, subtree: true });
})();
