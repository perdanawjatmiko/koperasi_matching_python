# koperasi-match

CLI Python untuk mencocokkan alamat gabungan pada workbook sumber dengan data koperasi dalam workbook referensi. Semua kolom pada baris referensi yang cocok dibawa ke sheet `MATCHED`.

Nama provinsi sumber selalu dibaca dari sel `A1` pada setiap sheet yang diproses. Contoh nilai yang didukung adalah `PROVINSI NAD`, `PROVINSI ACEH`, `PROVINSI SUMUT`, dan `PROVINSI SUMATRA UTARA`.

Dalam pencocokan kabupaten/kota, awalan administratif `KABUPATEN`, `KAB.`,
`KAB`, dan `KOTA` diabaikan. Contohnya, `ACEH BESAR` cocok dengan
`Kabupaten Aceh Besar`. Keterangan provinsi dalam kurung seperti `Aceh (NAD)`
juga dinormalisasi menjadi `ACEH`.

Parser mengabaikan label administratif berikut sebelum membaca nama wilayah:

- Kecamatan: `KEC`, `KEC,`, dan `KEC.`
- Desa/kelurahan: `DES`, `DES,`, `DES.`, `DS`, `DS.`, `DESA`, `KEL.`, dan `KELURAHAN`
- Kabupaten: `KAB`, `KAB,`, dan `KAB.`

Provinsi `BANGKA BELITUNG` dan `KEPULAUAN BANGKA BELITUNG` diperlakukan sebagai
provinsi yang sama.

Alamat berlabel desa dan kecamatan tanpa kabupaten tetap dapat dicocokkan jika
kombinasi desa-kecamatan unik dalam provinsi. Alamat yang hanya memuat nama desa
tetap diparsing, tetapi selalu masuk `PERLU_REVIEW` agar kecamatan dan kabupaten
dikonfirmasi secara manual. Nama kabupaten majemuk seperti `REJANG LEBONG`
dipertahankan lengkap. Kata `KOTA` diabaikan hanya dalam perbandingan
kabupaten/kota; nama kecamatan seperti `KOTA PADANG` tetap dipertahankan.
Awalan lokal `PEKON` tetap ditampilkan sebagai bagian nama desa, tetapi versi
tanpa `PEKON` juga digunakan sebagai alias ketika mencari referensi.

Untuk alamat yang dipisahkan koma, tiga bagian pertama dibaca sebagai desa,
kecamatan, dan kabupaten. Bagian keempat dan seterusnya, seperti nama provinsi,
diabaikan karena provinsi sudah berasal dari sel `A1`.

## Instalasi

Membutuhkan Python 3.12 atau lebih baru.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Workbook referensi default harus tersedia di `docs/referensi_koperasi.xlsx`. Lokasinya dihitung dari root project sehingga command dapat dijalankan dari direktori mana pun.

## Penggunaan

Memproses seluruh sheet yang memiliki kolom `ALAMAT`:

```bash
koperasi-match match docs/cleaning19258.xlsx
```

Selama proses, CLI menampilkan tahap yang sedang berjalan, progress bar jumlah
baris, persentase, dan waktu eksekusi. Nama provinsi setiap sheet tetap dibaca
dari sel `A1`.

Gunakan `--sheet` hanya untuk membatasi sheet:

```bash
koperasi-match match docs/cleaning19258.xlsx --sheet NAD --sheet SUM-UT
```

Tanpa `--output`, laporan dibuat di `outputs/hasil_pencocokan_<timestamp>.xlsx`.
Timestamp selalu ditambahkan agar laporan sebelumnya tidak tertimpa.

Referensi lain:

```bash
koperasi-match match docs/cleaning19258.xlsx \
  --reference /path/referensi_lain.xlsx \
  --sheet ACEH --sheet SUMUT \
  --output /path/hasil.xlsx
```

Contoh `--output /path/hasil.xlsx` menghasilkan file seperti
`/path/hasil_20260910_143025.xlsx`.

Periksa struktur workbook:

```bash
koperasi-match inspect /path/file.xlsx
```

Gunakan `koperasi-match match --help` untuk seluruh opsi. Jika nama bertimestamp
yang sama sudah ada, aplikasi menambahkan nomor urut seperti `_2`.

## Cara pencocokan

Urutan pencocokan adalah exact provinsi–desa–kecamatan–kabupaten, kombinasi unik desa–kecamatan, alias, lalu fuzzy matching yang dibatasi berdasarkan provinsi dan wilayah yang tersedia. Nilai default fuzzy adalah threshold 90 dan margin kandidat 5.

Status otomatis:

- `MATCHED_EXACT`
- `MATCHED_UNIQUE_DESA_KECAMATAN`
- `MATCHED_ALIAS`
- `MATCHED_FUZZY`

Hasil yang belum aman dipilih masuk `PERLU_REVIEW`. Alamat yang tidak dapat diparsing atau tidak memiliki kandidat masuk `TIDAK_DITEMUKAN`.

## Output

- `RINGKASAN`: parameter dan jumlah setiap status.
- `MATCHED`: semua kolom asli referensi ditambah kolom audit.
- `PERLU_REVIEW`: tiga kandidat terbaik dan skor.
- `TIDAK_DITEMUKAN`: alamat serta alasan kegagalan.

Kebijakan duplikasi record referensi yang sama dapat diatur dengan `--duplicate-policy keep|first|error`.

## Alias

Alias provinsi dan wilayah berada di `src/koperasi_match/normalizer.py`. Tambahkan pasangan nama baru ke `PROVINCE_ALIASES` atau `REGION_ALIASES`, lalu tambahkan pengujiannya.

## Batasan

- Parser berbasis aturan dan tidak memakai layanan internet atau AI.
- Alamat tanpa struktur yang cukup akan masuk pemeriksaan manual.
- Fuzzy match tidak menjamin nama administratif telah diperbarui; periksa sheet `PERLU_REVIEW`.
