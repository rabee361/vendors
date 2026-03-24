document.addEventListener('DOMContentLoaded', function () {
  var hamburger = document.getElementById('hamburger-btn');
  var sidebar = document.getElementById('sidebar');
  var backdrop = document.getElementById('sidebar-backdrop');

  function openSidebar() {
    sidebar.classList.add('open');
    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    backdrop.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (hamburger) {
    hamburger.addEventListener('click', function () {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });
});
