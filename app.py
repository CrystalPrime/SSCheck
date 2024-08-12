import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io
st.title("SS TAKİP MODÜLÜ")

st.markdown(
    """
    <style>

    .fixed-text-right {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 14px;
        color: #fafafa;
        background-color: #586e75;
        padding: 5px 10px;
        border-radius: 5px;
        font-family: 'Arial', sans-serif;
        z-index: 9999;
    }

    .fixed-text-left {
        position: fixed;
        bottom: 10px;
        left: 10px;
        font-size: 14px;
        color: #fafafa;
        background-color: #586e75;
        padding: 5px 10px;
        border-radius: 5px;
        font-family: 'Arial', sans-serif;
        z-index: 9999;
    }
    </style>

    <div class="fixed-text-right">Kızılaykart Bilgi Yönetimi</div>
    <div class="fixed-text-left">Batuhan Aydın</div>
    """,
    unsafe_allow_html=True
)


def ODKCaller(username, password):
    url = "https://odk.kizilay.org.tr/v1/projects/8/forms/SS%26amp%3B%2339%3B24%20ODK%20Form%20as%C4%B1l.svc/Submissions"
    odata_api_url = url

    params = {"$select": "*", "$top": 100000}
    
    auth_info = (username, password)

    headers = {
        "Accept": "application/json"
    }

    all_data = []

    while True:
        response = requests.get(odata_api_url, headers=headers, auth=auth_info, params=params)

        if response.status_code == 200:
            data = response.json()
            submissions_data = data.get("value", [])
            all_data.extend(submissions_data)
            if "@odata.nextLink" in data:
                odata_api_url = data["@odata.nextLink"]
            else:
                break
        else:
            st.error(f"İstek başarısız. Hata kodu: {response.status_code}")
            st.error(response.text)
            break

    def flatten_json(json_data, parent_key='', separator='_'):
        items = {}
        for key, value in json_data.items():
            new_key = parent_key + separator + key if parent_key else key
            if isinstance(value, dict):
                items.update(flatten_json(value, new_key, separator))
            else:
                items[new_key] = value
        return items

    flattened_data = [flatten_json(data) for data in all_data]

    df = pd.DataFrame(flattened_data)
    
    df = df.rename(columns={
        '__system_submissionDate': 'submission_date',
        'section_1_Q1_2': 'Operatör Adı',
        # İstediğiniz diğer sütun isimlerini de buraya ekleyebilirsiniz
    })
    
    return df

def ODKShow():
    deger = "@kizilay.org.tr"
    if deger in username:
        username_f = username
    else:
        username_f = username + deger
        
    df = ODKCaller(username_f, password)
    df['submission_date'] = pd.to_datetime(df['submission_date']).dt.date
    grouped = df.groupby(['Operatör Adı', 'submission_date']).size().reset_index(name='GIRIS_SAYISI')
    pivot_table = grouped.pivot(index='Operatör Adı', columns='submission_date', values='GIRIS_SAYISI').fillna(0)
    
    pivot_table['TOPLAM'] = pivot_table.sum(axis=1)
    
    total_sum = len(df[df["finished_survey"] == "yes"])
    no_count = len(df[df["finished_survey"] != "yes"])
    
    st.write(f"Tamamlanan Çağrı Sayısı: {total_sum}")
    st.write(f"Kalan Anket Sayısı: {no_count}")
    
    st.write("Operator Anket Sayısı:")
    st.dataframe(pivot_table)


    colors = plt.cm.tab20.colors  
    selected_columns = pivot_table.loc[:, pivot_table.columns != 'TOPLAM']
 
    fig, ax = plt.subplots(figsize=(20, 12))
    selected_columns.T.plot(kind='line', ax=ax, color= colors)  # Transpose ederek tarihleri x eksenine yerleştiriyoruz
    ax.set_title('Operatör Anket Sayısı (Zaman İçinde)')
    ax.set_xlabel('Tarih')
    ax.set_ylabel('Giriş Sayısı')
    ax.legend(loc='upper right') 
    st.pyplot(fig)
    
    st.write("Veri İstatistikleri:")
    st.write(pivot_table.describe())
    
    province_district_table = df.groupby(['section_1_province', 'section_1_district']).size().reset_index(name='count')
    province_district_table = province_district_table.rename(columns={
    'section_1_province': 'İL ADI',
    'section_1_district': 'İLÇE ADI',
    # İstediğiniz kadar sütun ismi ekleyebilirsiniz
    })
    
    st.write("İl İlçe Kırılım Tablosu:")
    st.dataframe(province_district_table)
    
    selected_column_for_plot = "Q0_confirmation"
    
    if df[selected_column_for_plot].dtype == 'object' or df[selected_column_for_plot].dtype == 'category':
        fig, ax = plt.subplots()

        counts = df[selected_column_for_plot].value_counts()
        labels = counts.index
        sizes = counts.values

        def autopct_func(pct):
            total = sum(sizes)
            val = int(round(pct*total/100.0))
            return f'{pct:.1f}% ({val})'

        ax.pie(sizes, labels=labels, autopct=autopct_func)
        ax.set_title(f"Anket Doluluk Grafiği")
        st.pyplot(fig)

    selected_column_for_plot_2 = "section_1_Q1_3a"
    selected_column_for_plot_3 = "section_1_Q1_3"
    if df[selected_column_for_plot_2].dtype == 'object' or df[selected_column_for_plot_2].dtype == 'category':
        fig, ax = plt.subplots()
        df1 = df[df['finished_survey'] == 'yes']
        value_counts_3a =  df1[selected_column_for_plot_2].value_counts()
        no_counts_3 = df1[selected_column_for_plot_3].value_counts().get('no', 0)
        labels = list(value_counts_3a.index) + ['section_1_Q1_3 (no)']
        sizes = list(value_counts_3a.values) + [no_counts_3]
        colors = ['#ff9999','#66b3ff', '#99ff99', '#ffcc99']
        
        def autopct_func(pct):
            total = sum(sizes)
            val = int(round(pct*total/100.0))
            return f'{pct:.1f}% ({val})'

        ax.pie(sizes, labels=labels, autopct=autopct_func, colors= colors)
        ax.set_title(f"Proje Kırılımı Grafiği")
        st.pyplot(fig)
        
    xlsx_io = io.BytesIO()
    with pd.ExcelWriter(xlsx_io, engine='xlsxwriter') as writer:
        grouped.to_excel(writer, index=False)

    xlsx_io.seek(0)
    st.download_button(
        label="SS verilerini Excel olarak indir",
        data=xlsx_io,
        file_name='SS_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

if 'username' not in st.session_state:
    st.session_state.username = ''
    st.session_state.password = ''
    st.session_state.logged_in = False

with st.form("login_form"):
    st.write("Lütfen kullanıcı adı ve şifrenizi girin:")
    username = st.text_input("Kullanıcı Adı", value=st.session_state.username)
    password = st.text_input("Şifre", type="password", value=st.session_state.password)
    submit_button = st.form_submit_button("Giriş")

if submit_button:
    if username and password:
        st.session_state.username = username
        st.session_state.password = password
        st.session_state.logged_in = True
        
        ODKShow()
        
    else:
        st.error("Lütfen kullanıcı adı ve şifrenizi girin.")
elif st.session_state.logged_in:
    ODKShow()
