(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // бургер
  var burger = $('[data-burger]'), nav = $('[data-nav]');
  if (burger) burger.addEventListener('click', function () {
    var o = nav.classList.toggle('open'); burger.setAttribute('aria-expanded', o);
  });
  // выпадающие меню (тач)
  $$('.dd__b').forEach(function (b) {
    b.addEventListener('click', function () {
      var d = b.parentNode, o = d.classList.toggle('open'); b.setAttribute('aria-expanded', o);
    });
  });

  // теги: «Все категории» / «Все услуги» без перезагрузки
  $$('[data-tags]').forEach(function (box) {
    var btn = $('[data-expand]', box);
    if (!btn) return;
    if (!$('.is-extra', box)) { btn.hidden = true; return; }
    btn.addEventListener('click', function () {
      var o = box.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', o);
      btn.textContent = o ? btn.dataset.less : btn.dataset.more;
    });
  });

  // формы обратного звонка
  $$('[data-cb]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = f.elements.name, phone = f.elements.phone;
      var nOk = name.value.trim().length > 1;
      var pOk = phone.value.replace(/\D/g, '').length >= 10;
      name.classList.toggle('err', !nOk);
      phone.classList.toggle('err', !pOk);
      if (!nOk || !pOk) return;
      // TODO бэкенд: отправить {name, phone, page} на обработчик заявок
      $('.cb__ok', f).hidden = false; f.reset();
    });
  });
  $$('[data-open-order]').forEach(function (a) {
    a.addEventListener('click', function () {
      setTimeout(function () { var i = $('#order input'); if (i) i.focus({ preventScroll: true }); }, 400);
    });
  });

  // слайдер похожих анкет
  $$('[data-slider]').forEach(function (s) {
    var t = $('[data-sl-track]', s);
    function step() { var c = t.firstElementChild; return c ? c.getBoundingClientRect().width + 20 : 300; }
    $('[data-sl-prev]', s).addEventListener('click', function () { t.scrollBy({ left: -step(), behavior: 'smooth' }); });
    $('[data-sl-next]', s).addEventListener('click', function () { t.scrollBy({ left: step(), behavior: 'smooth' }); });
  });

  // лайтбокс
  var lb = $('[data-lb]'), items = $$('[data-lb-item]'), cur = 0;
  if (lb && items.length) {
    var img = $('[data-lb-img]', lb);
    var show = function (i) { cur = (i + items.length) % items.length; img.src = items[cur].href; };
    var close = function () { lb.hidden = true; document.body.style.overflow = ''; };
    items.forEach(function (a, i) {
      a.addEventListener('click', function (e) { e.preventDefault(); show(i); lb.hidden = false; document.body.style.overflow = 'hidden'; });
    });
    $('[data-lb-close]', lb).addEventListener('click', close);
    $('[data-lb-prev]', lb).addEventListener('click', function () { show(cur - 1); });
    $('[data-lb-next]', lb).addEventListener('click', function () { show(cur + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(cur - 1);
      if (e.key === 'ArrowRight') show(cur + 1);
    });
  }
})();
