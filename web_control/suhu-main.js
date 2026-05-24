/**
 * suhu-main.js
 * File ini berisi logika rendering, chart, dan event handling.
 * Tidak perlu diubah saat mengganti sumber data.
 */

// ========== GLOBAL STATE ==========
let currentKandang = 1;
let currentChart = null;
let updateInterval = null;

// ========== FUNGSI BANTU ==========
function calculateTargetTemp(fase) {
    return SuhuData.FASE_TARGET[fase]?.target || 30;
}

function getRekomendasiText(fase, jenis) {
    let text = '';
    if (fase === 'doc') text = '🟡 Fase DOC: Butuh pemanas (bruder) dengan suhu 32-34°C. Pastikan ayam menyebar merata.';
    else if (fase === 'brooding') text = '🟢 Fase Brooding: Mulai kurangi pemanas bertahap. Suhu ideal 29-32°C.';
    else text = '🔵 Fase Grower: Pemanas sudah bisa dilepas. Jaga ventilasi dan suhu 26-29°C.';
    
    if (jenis === 'kampung') text += ' Ayam kampung lebih tahan terhadap suhu ekstrem.';
    else if (jenis === 'layer') text += ' Ayam layer sensitif terhadap perubahan suhu mendadak.';
    else text += ' Ayam broiler perlu suhu stabil untuk pertumbuhan optimal.';
    
    return text;
}

// ========== RENDER KONTEN KANDANG ==========
function renderKandangContent() {
    const settings = SuhuData.kandangSettings[currentKandang];
    const targetTemp = calculateTargetTemp(settings.fase);
    const range = SuhuData.JENIS_RANGE[settings.jenis];
    const fase = SuhuData.FASE_TARGET[settings.fase];
    const suhuHistory = SuhuData.kandangSuhuData[currentKandang] || SuhuData.kandangSuhuData[1];
    
    const html = `
        <!-- Grafik -->
        <div class="bg-white rounded-xl shadow-md p-4 mb-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-sm font-semibold text-gray-700">
                    <i class="fa-solid fa-chart-line text-amber-600"></i> 
                    Grafik Suhu Kandang ${currentKandang} (12 Jam Terakhir)
                </h3>
                <span class="text-xs text-gray-400"><i class="fa-regular fa-clock"></i> Update 5 detik</span>
            </div>
            <div class="chart-container-custom">
                <canvas id="suhuChart"></canvas>
            </div>
        </div>
        
        <!-- 4 Kartu Info -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div class="stat-card bg-white rounded-xl shadow-md p-4">
                <div class="bg-orange-100 p-2 rounded-lg w-fit mb-2"><i class="fa-solid fa-thermometer-half text-amber-600"></i></div>
                <p class="text-gray-500 text-xs">Suhu Saat Ini</p>
                <p class="text-2xl font-bold"><span id="currentTemp">--</span>°C</p>
                <span class="text-xs text-gray-400" id="tempStatus">--</span>
            </div>
            <div class="stat-card bg-white rounded-xl shadow-md p-4">
                <div class="bg-blue-100 p-2 rounded-lg w-fit mb-2"><i class="fa-solid fa-bullseye text-blue-500"></i></div>
                <p class="text-gray-500 text-xs">Suhu Target</p>
                <p class="text-2xl font-bold"><span id="targetTemp">${targetTemp}</span>°C</p>
                <p class="text-xs text-gray-400">Rentang: <span id="suhuRange">${fase.range}</span>°C (${range.nama})</p>
            </div>
            <div class="stat-card bg-white rounded-xl shadow-md p-4">
                <div class="bg-green-100 p-2 rounded-lg w-fit mb-2"><i class="fa-solid fa-calendar-week text-green-500"></i></div>
                <p class="text-gray-500 text-xs">Usia Ayam</p>
                <p class="text-2xl font-bold"><span id="usiaAyam">${fase.usia}</span> <span class="text-sm">Hari</span></p>
                <p class="text-xs text-gray-400" id="usiaText">${fase.usiaText}</p>
            </div>
            <div class="stat-card bg-white rounded-xl shadow-md p-4">
                <div class="bg-purple-100 p-2 rounded-lg w-fit mb-2"><i class="fa-solid fa-chicken text-purple-500"></i></div>
                <p class="text-gray-500 text-xs">Jenis & Fase</p>
                <p class="text-sm font-bold" id="jenisFase">${range.nama} - ${fase.fase}</p>
                <p class="text-xs text-gray-400" id="faseDesc">${settings.fase === 'doc' ? 'Masa awal, perlu pemanas' : (settings.fase === 'brooding' ? 'Adaptasi, pemanas dikurangi' : 'Penggemukan, cukup ventilasi')}</p>
            </div>
        </div>
        
        <!-- PENGATURAN -->
        <div class="bg-white rounded-xl shadow-md p-5">
            <div class="mb-6">
                <label class="text-sm font-semibold text-gray-800 flex items-center gap-2 mb-3">
                    <i class="fa-solid fa-dog text-amber-600"></i> Jenis Ayam
                </label>
                <div class="grid grid-cols-3 gap-3">
                    ${renderJenisButtons(settings.jenis)}
                </div>
            </div>
            
            <div class="mb-5">
                <label class="text-sm font-semibold text-gray-800 flex items-center gap-2 mb-3">
                    <i class="fa-solid fa-calendar-alt text-amber-600"></i> Fase Usia Ayam
                </label>
                <div class="grid grid-cols-3 gap-3">
                    ${renderFaseButtons(settings.fase)}
                </div>
            </div>
            
            <div class="mt-5 pt-3 border-t border-gray-100">
                <button id="confirmBtn" class="confirm-btn w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2">
                    <i class="fa-solid fa-check-circle"></i>
                    <span>OKE - Terapkan Pengaturan untuk Kandang ${currentKandang}</span>
                </button>
                <p class="text-xs text-gray-400 text-center mt-3">
                    <i class="fa-solid fa-circle-info"></i> Pengaturan disimpan per kandang
                </p>
            </div>
        </div>
        
        <div class="mt-5 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <p class="text-xs text-gray-600 flex items-start gap-2">
                <i class="fa-solid fa-lightbulb text-amber-500 mt-0.5"></i>
                <span id="rekomendasiText">${getRekomendasiText(settings.fase, settings.jenis)}</span>
            </p>
        </div>
    `;
    
    document.getElementById('kandangContent').innerHTML = html;
    initChartForCurrentKandang(suhuHistory);
    attachEventListeners();
    updateRealtimeDisplay();
}

function renderJenisButtons(activeJenis) {
    const jenisList = [
        { id: 'broiler', nama: 'Broiler', icon: 'fa-drumstick-bite', range: '28-33°C' },
        { id: 'layer', nama: 'Layer', icon: 'fa-egg', range: '27-30°C' },
        { id: 'kampung', nama: 'Kampung', icon: 'fa-feather-alt', range: '26-35°C' }
    ];
    
    return jenisList.map(j => `
        <button data-jenis="${j.id}" class="jenis-btn text-center p-2 rounded-lg transition-all ${activeJenis === j.id ? 'bg-amber-500 text-white border-amber-500' : 'bg-gray-100 border-gray-300 text-gray-700'} border-2">
            <i class="fa-solid ${j.icon} text-sm"></i>
            <p class="text-xs font-semibold mt-1">${j.nama}</p>
            <p class="text-[9px] opacity-70">${j.range}</p>
        </button>
    `).join('');
}

function renderFaseButtons(activeFase) {
    const faseList = [
        { id: 'doc', nama: 'DOC (0-7 hr)', icon: 'fa-egg', range: '32-34°C', color: 'text-green-600' },
        { id: 'brooding', nama: 'Brooding (8-21 hr)', icon: 'fa-chick', range: '29-32°C', color: 'text-yellow-600' },
        { id: 'grower', nama: 'Grower (>21 hr)', icon: 'fa-chicken', range: '26-29°C', color: 'text-orange-600' }
    ];
    
    return faseList.map(f => `
        <button data-fase="${f.id}" class="fase-btn text-center p-3 rounded-xl transition-all ${activeFase === f.id ? 'bg-orange-50 border-amber-500 active' : 'bg-gray-50 border-gray-200'} border-2">
            <i class="fa-solid ${f.icon} ${f.color} text-lg block mb-1"></i>
            <p class="text-xs font-semibold">${f.nama}</p>
            <p class="text-[10px] text-amber-600">${f.range}</p>
        </button>
    `).join('');
}

// ========== CHART ==========
function initChartForCurrentKandang(suhuHistory) {
    const ctx = document.getElementById('suhuChart')?.getContext('2d');
    if (!ctx) return;
    if (currentChart) currentChart.destroy();
    
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: SuhuData.jamLabels,
            datasets: [{
                label: `Suhu Kandang ${currentKandang}`,
                data: suhuHistory,
                borderColor: '#d97706',
                backgroundColor: 'rgba(217,119,6,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: '#facc15'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { min: 22, max: 38, ticks: { stepSize: 3, callback: v => v + '°C' } } }
        }
    });
}

// ========== UPDATE DATA REAL-TIME ==========
async function updateRealtimeDisplay() {
    const settings = SuhuData.kandangSettings[currentKandang];
    const targetTemp = calculateTargetTemp(settings.fase);
    
    // Ambil data terbaru dari mikrokontroler
    const latestData = await SuhuData.fetchLatestSuhuFromMCU(currentKandang);
    const currentTemp = latestData.suhu;
    
    // Update history
    if (!SuhuData.kandangSuhuData[currentKandang]) {
        SuhuData.kandangSuhuData[currentKandang] = [];
    }
    SuhuData.kandangSuhuData[currentKandang].push(currentTemp);
    if (SuhuData.kandangSuhuData[currentKandang].length > 12) {
        SuhuData.kandangSuhuData[currentKandang].shift();
    }
    
    // Update tampilan suhu saat ini
    const tempSpan = document.getElementById('currentTemp');
    const statusSpan = document.getElementById('tempStatus');
    if (tempSpan) tempSpan.innerText = currentTemp;
    
    const diff = Math.abs(currentTemp - targetTemp);
    let status = '', color = '';
    if (diff <= 1.2) { status = 'Optimal'; color = 'green'; }
    else if (diff <= 2.5) { status = 'Normal'; color = 'yellow'; }
    else { status = 'Waspada'; color = 'red'; }
    
    if (statusSpan) statusSpan.innerHTML = `<i class="fa-solid fa-circle text-${color}-500 text-[8px]"></i> ${status}`;
    
    // Update chart
    if (currentChart) {
        currentChart.data.datasets[0].data = SuhuData.kandangSuhuData[currentKandang];
        currentChart.update('none');
    }
}

// ========== EVENT HANDLER ==========
function attachEventListeners() {
    // Pilih jenis ayam
    document.querySelectorAll('.jenis-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const jenis = btn.getAttribute('data-jenis');
            if (jenis) {
                SuhuData.kandangSettings[currentKandang].jenis = jenis;
                document.querySelectorAll('.jenis-btn').forEach(b => {
                    b.classList.remove('bg-amber-500', 'text-white', 'border-amber-500');
                    b.classList.add('bg-gray-100', 'text-gray-700', 'border-gray-300');
                });
                btn.classList.remove('bg-gray-100', 'text-gray-700', 'border-gray-300');
                btn.classList.add('bg-amber-500', 'text-white', 'border-amber-500');
            }
        });
    });
    
    // Pilih fase
    document.querySelectorAll('.fase-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const fase = btn.getAttribute('data-fase');
            if (fase) {
                SuhuData.kandangSettings[currentKandang].fase = fase;
                document.querySelectorAll('.fase-btn').forEach(b => {
                    b.classList.remove('border-amber-500', 'bg-orange-50', 'active');
                    b.classList.add('border-gray-200', 'bg-gray-50');
                });
                btn.classList.remove('border-gray-200', 'bg-gray-50');
                btn.classList.add('border-amber-500', 'bg-orange-50', 'active');
            }
        });
    });
    
    // Tombol konfirmasi
    const confirmBtn = document.getElementById('confirmBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            renderKandangContent();
            confirmBtn.innerHTML = '<i class="fa-solid fa-check-circle"></i> <span>Berhasil Diterapkan!</span>';
            setTimeout(() => {
                if (document.getElementById('confirmBtn')) {
                    document.getElementById('confirmBtn').innerHTML = `<i class="fa-solid fa-check-circle"></i> <span>OKE - Terapkan Pengaturan untuk Kandang ${currentKandang}</span>`;
                }
            }, 1500);
        });
    }
}

// ========== NAVIGASI KANDANG ==========
function switchKandang(kandangId) {
    currentKandang = kandangId;
    renderKandangContent();
    
    document.querySelectorAll('.kandang-tab').forEach(tab => {
        tab.classList.remove('active', 'bg-amber-500', 'text-white', 'border-amber-500');
        tab.classList.add('bg-gray-100', 'text-gray-700', 'border-gray-200');
        if (tab.getAttribute('data-kandang') == kandangId) {
            tab.classList.remove('bg-gray-100', 'text-gray-700', 'border-gray-200');
            tab.classList.add('active', 'bg-amber-500', 'text-white', 'border-amber-500');
        }
    });
}

// ========== SIDEBAR KOMUNIKASI ==========
const sidebarIframe = document.getElementById('sidebarIframe');
function sendToSidebar(type, data = {}) { 
    if (sidebarIframe?.contentWindow) 
        sidebarIframe.contentWindow.postMessage({ type, ...data }, '*'); 
}

document.getElementById('mobileMenuBtn')?.addEventListener('click', () => sendToSidebar('toggleSidebar'));

window.addEventListener('message', (event) => {
    const data = event.data;
    if (data?.type === 'navigate') {
        if (data.page === 'welcome') window.location.href = 'dashboard.html';
        if (data.page === 'pakan') window.location.href = 'pakan.html';
        if (data.page === 'suhu') window.location.href = 'suhu.html';
    }
    if (data?.type === 'logout') { 
        if (confirm('Yakin keluar?')) window.location.href = 'login.html'; 
    }
});

sendToSidebar('setActive', { page: 'suhu' });

// ========== EVENT LISTENER TAB KANDANG ==========
document.addEventListener('click', (e) => {
    const tab = e.target.closest('.kandang-tab');
    if (tab) {
        const kandangId = parseInt(tab.getAttribute('data-kandang'));
        if (kandangId && kandangId !== currentKandang) switchKandang(kandangId);
    }
});

// ========== INITIALIZATION ==========
renderKandangContent();

// Update data real-time setiap 5 detik
setInterval(() => updateRealtimeDisplay(), 5000);

window.addEventListener('resize', () => { if (currentChart) currentChart.resize(); });