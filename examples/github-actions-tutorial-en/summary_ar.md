**ملخص دورة GitHub Actions وتطبيقها على مشروع Java + Gradle**

- GitHub Actions هو منصة لأتمتة سير عمل المطورين (ليس مجرد أداة CI/CD) وتدعم جميع أحداث GitHub مثل إنشاء issue، طلب pull، دمج، وإضافة مساهم.  
- يمكن ربط كل حدث بمجموعة من **actions** لتشكيل **workflow** يُنفّذ مهام مثل وضع labels، تعيين issues، تشغيل سكريبتات، بناء واختبار الكود.  
- الفوائد الرئيسة لاستخدام GitHub Actions في CI/CD: لا حاجة لأدوات خارجية، تكامل مباشر مع المستودع، إعداد سهل لا يتطلب متخصص DevOps، ودعم واسع للغات وأدوات (Node.js, Docker, Maven, Gradle, AWS …).  
- القوالب المتوفرة في تبويب **Actions** تُصنّف إلى ثلاث فئات:  
  1. **Deployment workflows** – للنشر على السحابة أو أدوات الأتمتة.  
  2. **Continuous integration workflows** – للبناء والاختبار.  
  3. **Publish workflows** – لنشر المخرجات إلى مستودعات.  
- اختيار قالب (مثال “Java Gradle”) يُنشئ ملف YAML في `.github/workflows/` يحتوي على اسم workflow، أحداث التفعيل، ووظائف (jobs) تتضمن خطوات:  
  1. `actions/checkout` لسحب الكود.  
  2. `setup-java` لتثبيت نسخة Java (مثال `1.8`).  
  3. تعديل صلاحيات ملف Gradle wrapper.  
  4. تنفيذ `gradle build`.  
- كل وظيفة تُنفّذ على خادم GitHub مُدار (Ubuntu/Windows/macOS)؛ يمكن تشغيل وظائف متوازية أو تسلسلها باستخدام كلمة `needs`. يمكن استخدام **matrix** لتشغيل نفس الوظيفة على أنظمة تشغيل متعددة.  
- لإنشاء صورة Docker من ملف JAR ودفعها إلى مستودع خاص على Docker Hub:  
  - يُستَخدم الإجراء الجاهز `docker/build-push-action@v2`.  
  - يُحدد اسم السجل (`docker.io`)، اسم المستودع، وبيانات الاعتماد (username / password) المخزنة كـ **Secrets** في إعدادات المستودع.  
  - يُستَخدم فقط عامل Ubuntu لأنه يحتوي على Docker مُثبت مسبقًا.  
- بعد دمج الـ PR أو دفع تعديل إلى `master`، يُظهر GitHub Actions خطوات “Built with Gradle” ثم “Built and push Docker images”، وتظهر الصورة الجديدة في Docker Hub مع علامة (tag) تُستَند إلى اسم الفرع أو ما يُحدَّد يدويًا.  
- الدورة ستستكمل مواضيع أخرى مثل نشر الصور إلى سحابة/Kubernetes، اختبار وبناء تطبيقات Node.js، وأتمتة عمليات إضافية.  

**الخلاصة:** GitHub Actions يوفّر بيئة متكاملة وسهلة لإعداد CI/CD وأتمتة مهام التطوير، مع دعم واسع للغات، أدوات، ومستودعات Docker.

---
Source: https://www.youtube.com/watch?v=R8_veQiYBjI
