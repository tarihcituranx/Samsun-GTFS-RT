const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());

const YBS_BASE_URL = "https://ybs.samsun.bel.tr/service/";
const HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
};

let cachedToken = null;
let tokenExpiry = null;

// Self-healing YBS Token Fetcher
async function getToken() {
    if (cachedToken && tokenExpiry && new Date() < tokenExpiry) {
        return cachedToken;
    }

    try {
        const response = await axios.post(YBS_BASE_URL, 'method=getGuestToken', { headers: HEADERS, timeout: 10000 });
        if (response.data && response.data.token) {
            cachedToken = response.data.token;
            // 200s valid, cache for 180s
            tokenExpiry = new Date(new Date().getTime() + 180 * 1000);
            return cachedToken;
        }
    } catch (error) {
        console.error("YBS Token Error:", error.message);
    }
    return null;
}

// 1. Odak API
app.get('/api/odak', async (req, res) => {
    const token = await getToken();
    if (!token) return res.status(500).json({ status: "ERROR", message: "Token failed" });

    try {
        const response = await axios.get(`${YBS_BASE_URL}?method=odakSamsun_Crud&token=${token}`, {
            headers: { ...HEADERS, 'Referer': 'https://odak.samsun.bel.tr/' },
            timeout: 15000
        });
        res.json(response.data);
    } catch (e) {
        res.status(500).json({ status: "ERROR", error: e.message });
    }
});

// 2. SamAir Saatler
app.get('/api/samair/saatler/:hatid', async (req, res) => {
    const token = await getToken();
    if (!token) return res.status(500).json({ status: "ERROR", message: "Token failed" });

    try {
        const response = await axios.get(`${YBS_BASE_URL}?method=samair_ucaksefersaatleri_public&submethod=HatlarList&hatid=${req.params.hatid}&token=${token}`, {
            headers: HEADERS,
            timeout: 15000
        });
        res.json(response.data);
    } catch (e) {
        res.status(500).json({ status: "ERROR", error: e.message });
    }
});

// 3. SamAir Araclar
app.get('/api/samair/araclar', async (req, res) => {
    const token = await getToken();
    if (!token) return res.status(500).json({ status: "ERROR", message: "Token failed" });

    try {
        const response = await axios.get(`${YBS_BASE_URL}?method=samair_duraklar_public&submethod=araclar&token=${token}`, {
            headers: HEADERS,
            timeout: 15000
        });
        res.json(response.data);
    } catch (e) {
        res.status(500).json({ status: "ERROR", error: e.message });
    }
});

// Health check
app.get('/', (req, res) => res.send('YBS Proxy Backend is running.'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
