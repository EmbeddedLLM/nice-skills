/* Native Canvas keeps this starter offline. Replace drawArt with your algorithm. */
(function (root) {
  'use strict';
  function random(seed) {
    let state = seed >>> 0;
    return () => {
      state += 0x6D2B79F5;
      let t = state;
      t = Math.imul(t ^ t >>> 15, t | 1);
      t ^= t + Math.imul(t ^ t >>> 7, t | 61);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function drawArt(canvas, {seed = 12345, count = 160} = {}) {
    if (!Number.isInteger(seed) || !Number.isInteger(count) || count < 1 || count > 2000)
      throw new Error('Use an integer seed and count from 1 to 2000');
    const rand = random(seed), ctx = canvas.getContext('2d');
    ctx.fillStyle = '#faf9f6'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < count; i++) {
      const x = rand() * canvas.width, y = rand() * canvas.height;
      ctx.fillStyle = ['#284b63', '#d77a61', '#7d9d78'][Math.floor(rand()*3)];
      ctx.beginPath(); ctx.arc(x, y, 2 + rand()*18, 0, Math.PI*2); ctx.fill();
    }
  }
  root.SeededArt = {random, drawArt};
})(globalThis);
