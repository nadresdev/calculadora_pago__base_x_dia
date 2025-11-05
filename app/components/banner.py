import streamlit as st

def banner_reglas():
    """Banner en la parte superior de la app con las reglas y tarifas"""
    
    st.markdown("""
    <style>
    .banner-rules {
        background: linear-gradient(90deg, #1f77b4 0%, #2e8b57 100%);
        color: white;
        padding: 1rem;
        border-radius: 0 0 15px 15px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-bottom: 3px solid #ffd700;
    }
    .banner-title {
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .banner-content {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .banner-item {
        text-align: center;
        padding: 0.5rem 1rem;
        background: rgba(255,255,255,0.15);
        border-radius: 8px;
        min-width: 120px;
        backdrop-filter: blur(10px);
    }
    .banner-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-bottom: 0.3rem;
    }
    .banner-value {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .banner-highlight {
        background: rgba(255,215,0,0.2);
        border: 1px solid rgba(255,215,0,0.5);
    }
    /* Responsive */
    @media (max-width: 768px) {
        .banner-content {
            flex-direction: column;
            gap: 0.5rem;
        }
        .banner-item {
            min-width: 90%;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="banner-rules">
        <div class="banner-title">📊 REGLAS Y TARIFAS APLICADAS</div>
        <div class="banner-content">
            <div class="banner-item">
                <div class="banner-label">Hora Normal</div>
                <div class="banner-value">$15,500</div>
            </div>
            <div class="banner-item banner-highlight">
                <div class="banner-label">Bono 6 Horas</div>
                <div class="banner-value">$100,000</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Hora Extra</div>
                <div class="banner-value">$15,500</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Menos de 6h</div>
                <div style="font-size: 0.8rem;">Horas × $15,500</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Más de 6h</div>
                <div style="font-size: 0.8rem;">$100k + extras</div>
            </div>
            <div class="banner-item">
                <div class="banner-label">Recargos</div>
                <div style="font-size: 0.8rem;">+ Pago base</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)