import pandas as pd
import streamlit as st
import io

st.title("Transfer Planning Tool")

# Load Excel file
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file:
    try:
        data = pd.read_excel(uploaded_file)
        st.success("Excel file loaded successfully!")
        st.dataframe(data.head())

        if st.button("Generate Transfer List"):
            # Transfer listesi oluşturma işlemi
            grouped_data = data.groupby('Bölge Müdürü')
            transfer_list = []

            for manager, group in grouped_data:
                # İhtiyaçları ve transfer edilebilir stokları sırala
                group = group.sort_values(by=['İhtiyaç'], ascending=False)
                transfer_availability = group.set_index(['Depo Kodu', 'Madde Kodu'])['Transfer Edilebilir'].to_dict()

                for index, row in group.iterrows():
                    receiving_depot = row['Depo Kodu']
                    item_code = row['Madde Kodu']
                    needed_amount = row['İhtiyaç']

                    if needed_amount > 0:
                        # Aynı ürün kodu için transfer edilebilir stoğu en çok olan mağazadan başlayarak transfer yap
                        potential_senders = group[group['Madde Kodu'] == item_code].sort_values(by=['Transfer Edilebilir'], ascending=False)

                        for sending_index, sending_row in potential_senders.iterrows():
                            if needed_amount <= 0:
                                break
                            available_amount = transfer_availability[(sending_row['Depo Kodu'], item_code)]
                            if available_amount > 0:
                                transfer_amount = min(needed_amount, available_amount)
                                transfer_list.append({
                                    'Gönderen Depo': sending_row['Depo Kodu'],
                                    'Alan Depo': receiving_depot,
                                    'Madde Kodu': item_code,
                                    'Transfer Miktarı': transfer_amount
                                })
                                transfer_availability[(sending_row['Depo Kodu'], item_code)] -= transfer_amount
                                needed_amount -= transfer_amount

            transfer_df = pd.DataFrame(transfer_list)
            st.success("Transfer list generated successfully!")
            st.dataframe(transfer_df)

            # Transfer listesini indirmek için kullanıcıya sunma
            @st.cache_data
            def convert_df(df):
                return df.to_excel(index=False)

            # Excel dosyasını indirilebilir hale getirme
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                transfer_df.to_excel(writer, index=False)
                writer.close()

            st.download_button(
                label="Download Transfer List",
                data=buffer.getvalue(),
                file_name='Transfer_Listesi.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
    except Exception as e:
        st.error(f"Failed to load file: {e}")
