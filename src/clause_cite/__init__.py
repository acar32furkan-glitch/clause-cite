"""clause-cite — sözleşme metinlerini kanıtlı aksiyon maddelerine çeviren deterministik motor.

Tasarım ilkesi: **alıntısız madde yoktur.** Çıktıdaki her `Item`, kaynak belgede birebir geçen bir
metin (``quote``) ve bir satır aralığı (``citation``) taşır; ``verify`` komutu bu invaryantı
denetler. LLM çağrısı yoktur, ağa çıkılmaz ve "şimdi" dışarıdan ``--anchor`` ile enjekte edilir —
böylece aynı girdi her zaman aynı maddeleri üretir.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
