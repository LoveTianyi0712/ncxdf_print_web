// 移动端专用JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    initMobileFeatures();
});

function initMobileFeatures() {
    // 检测设备类型
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
    const isTouchDevice = 'ontouchstart' in window;

    // 初始化汉堡菜单
    if (isMobile) {
        initMobileMenu();
    }

    // 初始化触摸优化
    if (isTouchDevice) {
        initTouchOptimizations();
    }

    // 初始化响应式功能
    initResponsiveFeatures();

    // 监听屏幕方向变化
    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleResize);
}

// 汉堡菜单功能
function initMobileMenu() {
    // 创建汉堡菜单按钮
    const navbar = document.querySelector('.navbar .container-fluid');
    const navbarBrand = document.querySelector('.navbar-brand');
    
    if (navbar && !document.querySelector('.mobile-menu-toggle')) {
        const menuToggle = document.createElement('button');
        menuToggle.className = 'mobile-menu-toggle d-md-none';
        menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        menuToggle.setAttribute('aria-label', '打开菜单');
        
        // 在品牌logo后插入汉堡按钮
        navbarBrand.parentNode.insertBefore(menuToggle, navbarBrand.nextSibling);
        
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'mobile-overlay';
        document.body.appendChild(overlay);
        
        // 绑定事件
        menuToggle.addEventListener('click', toggleMobileMenu);
        overlay.addEventListener('click', closeMobileMenu);
        
        // 为侧边栏链接添加关闭菜单功能
        const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', closeMobileMenu);
        });
    }
}

function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const toggleBtn = document.querySelector('.mobile-menu-toggle i');
    
    if (sidebar && overlay) {
        const isOpen = sidebar.classList.contains('show');
        
        if (isOpen) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    }
}

function openMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const toggleBtn = document.querySelector('.mobile-menu-toggle i');
    
    if (sidebar && overlay && toggleBtn) {
        sidebar.classList.add('show');
        overlay.classList.add('show');
        toggleBtn.className = 'fas fa-times';
        document.body.style.overflow = 'hidden'; // 防止背景滚动
    }
}

function closeMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const toggleBtn = document.querySelector('.mobile-menu-toggle i');
    
    if (sidebar && overlay && toggleBtn) {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        toggleBtn.className = 'fas fa-bars';
        document.body.style.overflow = ''; // 恢复滚动
    }
}

// 触摸优化
function initTouchOptimizations() {
    // 为按钮添加触摸反馈
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        
        button.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('touch-active');
            }, 150);
        });
    });

    // 为导航链接添加触摸反馈
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('touchstart', function() {
            this.style.backgroundColor = '#287042';
            this.style.color = 'white';
        });
        
        link.addEventListener('touchend', function() {
            setTimeout(() => {
                if (!this.classList.contains('active')) {
                    this.style.backgroundColor = '';
                    this.style.color = '';
                }
            }, 150);
        });
    });

    // 优化滚动性能
    document.addEventListener('touchmove', function(e) {
        // 阻止默认的橡皮筋效果，但允许正常滚动
        if (e.target.closest('.sidebar') || e.target.closest('.content')) {
            // 允许侧边栏和内容区域滚动
            return;
        }
    }, { passive: true });
}

// 响应式功能
function initResponsiveFeatures() {
    // 自适应打印预览大小
    const printPreview = document.querySelector('.print-preview');
    if (printPreview) {
        const resizePreview = () => {
            const container = printPreview.parentElement;
            const containerWidth = container.offsetWidth;
            const isMobile = window.innerWidth <= 768;
            
            if (isMobile && containerWidth) {
                printPreview.style.maxWidth = (containerWidth - 30) + 'px';
            } else {
                printPreview.style.maxWidth = '';
            }
        };
        
        resizePreview();
        window.addEventListener('resize', resizePreview);
    }

    // 优化表格显示
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (window.innerWidth <= 576) {
            // 在小屏幕上简化表格显示
            const cells = table.querySelectorAll('td, th');
            cells.forEach(cell => {
                cell.style.fontSize = '0.85rem';
                cell.style.padding = '0.5rem';
            });
        }
    });

    // 优化表单布局
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const isMobile = window.innerWidth <= 768;
        const formGroups = form.querySelectorAll('.row > div');
        
        if (isMobile) {
            formGroups.forEach(group => {
                group.classList.add('mb-3');
            });
        }
    });
}

// 屏幕方向变化处理
function handleOrientationChange() {
    setTimeout(() => {
        // 重新计算布局
        initResponsiveFeatures();
        
        // 关闭移动菜单
        if (window.innerWidth <= 768) {
            closeMobileMenu();
        }
        
        // 调整视口高度
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', vh + 'px');
    }, 500);
}

// 窗口大小变化处理
function handleResize() {
    const isMobile = window.innerWidth <= 768;
    
    // 如果切换到桌面模式，关闭移动菜单
    if (!isMobile) {
        closeMobileMenu();
    }
    
    // 重新初始化响应式功能
    initResponsiveFeatures();
}

// 打印预览优化
function optimizePrintPreviewForMobile(imageUrl) {
    const printPreview = document.getElementById('printPreview');
    if (!printPreview) return;
    
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // 移动端显示优化
        printPreview.innerHTML = `
            <div class="mobile-print-preview">
                <div class="print-image-container">
                    <img src="${imageUrl}" alt="打印预览" class="img-fluid" style="border-radius: 8px;">
                </div>
                <div class="print-actions mt-3">
                    <button id="downloadBtn" class="btn btn-success w-100 mb-2">
                        <i class="fas fa-download me-2"></i>下载图片
                    </button>
                    <button class="btn btn-outline-primary w-100" onclick="zoomPrintPreview()">
                        <i class="fas fa-search-plus me-2"></i>放大查看
                    </button>
                </div>
            </div>
        `;
    } else {
        // 桌面端正常显示
        printPreview.innerHTML = `
            <div class="print-preview">
                <img src="${imageUrl}" alt="打印预览" class="img-fluid">
            </div>
        `;
    }
}

// 放大查看功能
function zoomPrintPreview() {
    const img = document.querySelector('.print-image-container img');
    if (!img) return;
    
    // 创建全屏查看模态框
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-fullscreen">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">打印预览</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
                </div>
                <div class="modal-body p-0 d-flex align-items-center justify-content-center">
                    <img src="${img.src}" alt="打印预览" class="img-fluid" style="max-height: 90vh;">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // 模态框关闭后移除元素
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

// 添加触摸手势支持
function addTouchGestures() {
    let startX, startY, distX, distY;
    
    document.addEventListener('touchstart', function(e) {
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        if (!startX || !startY) return;
        
        const touch = e.changedTouches[0];
        distX = touch.clientX - startX;
        distY = touch.clientY - startY;
        
        // 检测侧滑手势
        if (Math.abs(distX) > Math.abs(distY) && Math.abs(distX) > 50) {
            if (distX > 0 && startX < 50) {
                // 从左边缘右滑，打开菜单
                openMobileMenu();
            } else if (distX < 0 && document.querySelector('.sidebar.show')) {
                // 左滑，关闭菜单
                closeMobileMenu();
            }
        }
        
        startX = startY = null;
    }, { passive: true });
}

// 设置视口高度变量（解决移动端100vh问题）
function setViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', vh + 'px');
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 处理移动端版权信息和操作栏的位置关系
function handleMobileFooterPosition() {
    const isMobile = window.innerWidth <= 768;
    if (!isMobile) return;
    
    const footer = document.querySelector('footer');
    const actionBar = document.querySelector('.mobile-action-bar');
    
    if (footer && actionBar) {
        // 检查操作栏是否显示
        const actionBarVisible = actionBar.style.display !== 'none' && 
                                 getComputedStyle(actionBar).display !== 'none';
        
        if (actionBarVisible) {
            footer.style.bottom = '60px'; // 操作栏高度
        } else {
            footer.style.bottom = '0';
        }
    }
}

// 在窗口加载和大小变化时调用
window.addEventListener('load', handleMobileFooterPosition);
window.addEventListener('resize', handleMobileFooterPosition);

// 导出函数供其他脚本使用
window.mobileUtils = {
    toggleMobileMenu,
    openMobileMenu,
    closeMobileMenu,
    optimizePrintPreviewForMobile,
    zoomPrintPreview,
    setViewportHeight,
    handleMobileFooterPosition
}; 