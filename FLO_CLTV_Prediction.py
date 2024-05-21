##############################################################
# BG-NBD ve Gamma-Gamma ile CLTV Prediction
##############################################################
# İş Problemi (Business Problem)
###############################################################
# FLO satış ve pazarlama faaliyetleri için roadmap belirlemek istemektedir.
# Şirketin orta uzun vadeli plan yapabilmesi için var olan müşterilerin gelecekte şirkete sağlayacakları potansiyel değerin tahmin edilmesi
###############################################################
# Veri Seti Hikayesi
###############################################################
# Veri seti son alışverişlerini 2020 - 2021 yıllarında OmniChannel(hem online hem offline alışveriş yapan) olarak yapan müşterilerin geçmiş alışveriş davranışlarından
# elde edilen bilgilerden oluşmaktadır.

# master_id: Eşsiz müşteri numarası
# order_channel : Alışveriş yapılan platforma ait hangi kanalın kullanıldığı (Android, ios, Desktop, Mobile, Offline)
# last_order_channel : En son alışverişin yapıldığı kanal
# first_order_date : Müşterinin yaptığı ilk alışveriş tarihi
# last_order_date : Müşterinin yaptığı son alışveriş tarihi
# last_order_date_online : Muşterinin online platformda yaptığı son alışveriş tarihi
# last_order_date_offline : Muşterinin offline platformda yaptığı son alışveriş tarihi
# order_num_total_ever_online : Müşterinin online platformda yaptığı toplam alışveriş sayısı
# order_num_total_ever_offline : Müşterinin offline'da yaptığı toplam alışveriş sayısı
# customer_value_total_ever_offline : Müşterinin offline alışverişlerinde ödediği toplam ücret
# customer_value_total_ever_online : Müşterinin online alışverişlerinde ödediği toplam ücret
# interested_in_categories_12 : Müşterinin son 12 ayda alışveriş yaptığı kategorilerin listesi
###############################################################
import pandas as pd
import datetime as dt
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.2f' % x)
pd.set_option('display.width', 1000)

df_ = pd.read_csv("C:/Users/ipeks/PycharmProjects/pythonProject/WEEK3/ödev\FLOMusteriSegmentasyonu/flo_data_20k.csv")
df = df_.copy()
df.head(10)
df.columns
df.describe().T
df.isnull().sum()
df.info()


def outlier_thresholds(df, var):
    Q1 = df[var].quantile(0.01)
    Q3 = df[var].quantile(0.99)
    IQR = Q3 - Q1
    up_lim = Q3 + 1.5 * IQR
    low_lim = Q1 - 1.5 * IQR
    return low_lim, up_lim


def replace_with_thresholds(df, var):
    low_lim, up_lim = outlier_thresholds(df, var)
    df.loc[(df[var] < low_lim), var] = round(low_lim, 0)
    df.loc[(df[var] > up_lim), var] = round(up_lim, 0)


columns = ["order_num_total_ever_online", "order_num_total_ever_offline", "customer_value_total_ever_offline",
           "customer_value_total_ever_online"]
for col in columns:
    replace_with_thresholds(df, col)

#  Omnichannel müşterilerin hem online'dan hemde offline platformlardan alışveriş yaptığını ifade etmektedir.
#  Herbir müşterinin toplam alışveriş sayısı ve harcaması için yeni değişkenler oluşturuldu.
df["order_num_total"] = df["order_num_total_ever_online"] + df["order_num_total_ever_offline"]
df["customer_value_total"] = df["customer_value_total_ever_offline"] + df["customer_value_total_ever_online"]

df.info()
date_columns = df.columns[df.columns.str.contains("date")]
df[date_columns] = df[date_columns].apply(pd.to_datetime)
df.info()

# CLTV Veri Yapısının Oluşturulması
# recency: Son satın alma üzerinden geçen zaman. Haftalık. (kullanıcı özelinde)
# T: Müşterinin yaşı. Haftalık. (analiz tarihinden ne kadar süre önce ilk satın alma yapılmış)
# frequency: tekrar eden toplam satın alma sayısı (frequency>1)
# monetary: satın alma başına ortalama kazanç

# Veri setindeki en son alışverişin yapıldığı tarihten 2 gün sonrasını analiz tarihi olarak alındı.
df["last_order_date"].max()
analysis_date = dt.datetime(2021, 6, 1)

# customer_id, recency_cltv_weekly, T_weekly, frequency ve monetary_cltv_avg değerlerinin yer aldığı yeni bir cltv dataframe oluşturuldu.
# Monetary değeri satın alma başına ortalama değer olarak, recency ve tenure değerleri ise haftalık cinsten ifade edildi.
cltv_df = pd.DataFrame()
cltv_df["customer_id"] = df["master_id"]
cltv_df["recency_cltv_weekly"] = ((df["last_order_date"] - df["first_order_date"]).dt.days) / 7
cltv_df["T_weekly"] = ((analysis_date - df["first_order_date"]).dt.days) / 7
cltv_df["frequency"] = df["order_num_total"]
cltv_df["monetary_cltv_avg"] = df["customer_value_total"] / df["order_num_total"]

cltv_df.head()

#  BG/NBD, Gamma-Gamma Modellerinin Kurulması, CLTV'nin hesaplanması
#  BG/NBD modelini fit edilmesi
bgf = BetaGeoFitter(penalizer_coef=0.001)
bgf.fit(cltv_df['frequency'],
        cltv_df['recency_cltv_weekly'],
        cltv_df['T_weekly'])
# 3 ay içerisinde müşterilerden beklenen satın almaları tahmini ve exp_sales_3_month olarak cltv dataframe'ine ekleme
cltv_df["exp_sales_3_month"] = bgf.predict(4 * 3,
                                           cltv_df['frequency'],
                                           cltv_df['recency_cltv_weekly'],
                                           cltv_df['T_weekly'])
cltv_df.head()

# 6 ay içerisinde müşterilerden beklenen satın almaları tahmini ve exp_sales_6_month olarak cltv dataframe'ine ekleme.
cltv_df["exp_sales_6_month"] = bgf.predict(4 * 6,
                                           cltv_df['frequency'],
                                           cltv_df['recency_cltv_weekly'],
                                           cltv_df['T_weekly'])

# 3. ve 6.aydaki en çok satın alım gerçekleştirecek 10 kişi
cltv_df.sort_values("exp_sales_3_month", ascending=False)[:10]
cltv_df.sort_values("exp_sales_6_month", ascending=False)[:10]

#  Gamma-Gamma modelini fit etme. Müşterilerin ortalama bırakacakları değeri tahminleyip exp_average_value olarak cltv dataframe'ine ekleme.
ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(cltv_df['frequency'], cltv_df['monetary_cltv_avg'])
cltv_df["exp_average_value"] = ggf.conditional_expected_average_profit(cltv_df['frequency'],
                                                                       cltv_df['monetary_cltv_avg'])

# 6 aylık CLTV hesaplama ve cltv ismiyle dataframe'e ekleme.
cltv = ggf.customer_lifetime_value(bgf,
                                   cltv_df['frequency'],
                                   cltv_df['recency_cltv_weekly'],
                                   cltv_df['T_weekly'],
                                   cltv_df['monetary_cltv_avg'],
                                   time=6,
                                   freq="W",
                                   discount_rate=0.01)
cltv_df["cltv"] = cltv
# b. Cltv değeri en yüksek 20 kişiyi gözlemleyiniz.
cltv_df.sort_values("cltv", ascending=False)[:20]

#  CLTV'ye Göre Segmentlerin Oluşturulması
cltv_df["cltv_segment"] = pd.qcut(cltv_df["cltv"], 4, labels=["D", "C", "B", "A"])
cltv_df.head()
