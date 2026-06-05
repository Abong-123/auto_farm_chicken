/**
 * suhu-data.js
 * File ini berisi data dan konfigurasi suhu.
 * Untuk integrasi dengan mikrokontroler, cukup ganti file ini
 * atau ubah fungsi fetchData() untuk mengambil dari API.
 */

// ========== KONFIGURASI RENTANG SUHU PER JENIS AYAM ==========
const JENIS_RANGE = {
    broiler: { min: 28, max: 33, nama: 'Broiler' },
    layer: { min: 27, max: 30, nama: 'Layer' },
    kampung: { min: 26, max: 35, nama: 'Kampung' }
};

// ========== KONFIGURASI TARGET SUHU PER FASE (NILAI TENGAH) ==========
const FASE_TARGET = {
    doc: { 
        usia: 5, 
        usiaText: 'DOC (0-7 hari)', 
        fase: 'DOC', 
        target: 33,        // tengah dari 32-34
        range: '32-34',
        min: 32,
        max: 34
    },
    brooding: { 
        usia: 15, 
        usiaText: 'Brooding (8-21 hari)', 
        fase: 'Brooding', 
        target: 30.5,      // tengah dari 29-32
        range: '29-32',
        min: 29,
        max: 32
    },
    grower: { 
        usia: 30, 
        usiaText: 'Grower (>21 hari)', 
        fase: 'Grower', 
        target: 27.5,      // tengah dari 26-29
        range: '26-29',
        min: 26,
        max: 29
    }
};

// ========== DATA DUMMY UNTUK SIMULASI (NANTI DIGANTI DENGAN DATA REAL DARI MIKROKONTROLER) ==========

// Data suhu per kandang (history 12 jam)
let kandangSuhuData = {
    1: [32.1, 32.5, 32.8, 32.3, 31.9, 32.2, 32.6, 33.0, 32.7, 32.4, 32.1, 31.8],
    2: [30.5, 30.8, 31.0, 30.7, 30.3, 30.6, 30.9, 31.2, 30.8, 30.5, 30.2, 30.0],
    3: [29.0, 29.3, 29.5, 29.1, 28.8, 29.2, 29.6, 29.4, 29.0, 28.7, 28.5, 28.3],
    4: [31.0, 31.2, 31.5, 31.1, 30.8, 31.0, 31.3, 31.6, 31.2, 30.9, 30.6, 30.4],
    5: [28.5, 28.7, 29.0, 28.6, 28.3, 28.5, 28.8, 29.1, 28.7, 28.4, 28.1, 27.9]
};

// Label waktu untuk grafik (12 jam terakhir)
function generateTimeLabels() {
    const labels = [];
    for (let i = 11; i >= 0; i--) {
        let d = new Date();
        d.setHours(d.getHours() - i);
        labels.push(d.getHours() + ':00');
    }
    return labels;
}

let jamLabels = generateTimeLabels();

// Pengaturan aktif per kandang (jenis ayam, fase, dan batas suhu)
let kandangSettings = {
    1: { jenis: 'broiler', fase: 'doc', suhuMin: 32, suhuMax: 34 },
    2: { jenis: 'broiler', fase: 'brooding', suhuMin: 29, suhuMax: 32 },
    3: { jenis: 'layer', fase: 'grower', suhuMin: 26, suhuMax: 29 },
    4: { jenis: 'kampung', fase: 'doc', suhuMin: 32, suhuMax: 34 },
    5: { jenis: 'broiler', fase: 'grower', suhuMin: 26, suhuMax: 29 }
};

// ========== FUNGSI UNTUK MENGAMBIL DATA DARI MIKROKONTROLER ==========
// NANTI FUNGSI INI DIGANTI DENGAN FETCH REAL

/**
 * Fungsi untuk mengambil data suhu terbaru dari mikrokontroler.
 * Format response yang diharapkan:
 * {
 *   "kandang_id": 1,
 *   "suhu": 32.5,
 *   "timestamp": "2026-05-24 14:30:00"
 * }
 */
async function fetchLatestSuhuFromMCU(kandangId) {
    // SIMULASI: data dummy (nanti diganti dengan fetch real)
    // return await fetch(`http://localhost:3000/api/suhu/${kandangId}`).then(res => res.json());
    
    // SEMENTARA: generate data simulasi
    const settings = kandangSettings[kandangId];
    const targetTemp = FASE_TARGET[settings.fase].target;
    const hour = new Date().getHours();
    let heatBonus = (hour >= 12 && hour <= 14) ? 1.2 : ((hour >= 22 || hour <= 5) ? -0.8 : 0);
    let temp = targetTemp + heatBonus + (Math.random() - 0.5) * 1.2;
    const range = JENIS_RANGE[settings.jenis];
    temp = Math.min(range.max + 2, Math.max(range.min - 2, temp));
    
    return {
        kandang_id: kandangId,
        suhu: Math.round(temp * 10) / 10,
        timestamp: new Date().toISOString()
    };
}

// Fungsi untuk mendapatkan data history (nanti dari database)
async function fetchHistorySuhu(kandangId) {
    // SEMENTARA: pakai data dummy
    // NANTI: fetch dari API history
    return kandangSuhuData[kandangId] || kandangSuhuData[1];
}

// ========== EKSPOR GLOBAL ==========
window.SuhuData = {
    JENIS_RANGE,
    FASE_TARGET,
    kandangSuhuData,
    jamLabels,
    kandangSettings,
    fetchLatestSuhuFromMCU,
    fetchHistorySuhu,
    generateTimeLabels
};