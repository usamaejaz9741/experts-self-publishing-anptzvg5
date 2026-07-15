// function handleFormSubmission(formSelector) {
//     $(formSelector).submit(function (e) {
//         e.preventDefault();

//         if (!validateForm(formSelector)) {
//             console.log("sad");

//             Swal.fire({
//                 icon: 'error',
//                 title: 'Missing Required Information',
//                 text: 'Please ensure all required fields are filled in before submitting.',
//                 showConfirmButton: false,
//             });
//             return;
//         }

//         var formData = $(this).serialize();
//         var formAction = $(this).attr('action');

//         Swal.fire({
//             title: 'Processing...',
//             text: 'Please wait while we submit your form.',
//             allowOutsideClick: false,
//             didOpen: () => {
//                 Swal.showLoading();
//             }
//         });

//         $.ajax({
//             url: formAction,
//             type: "POST",
//             data: formData,
//             success: function (response) {
//                 if (response.status === "success") {
//                     Swal.fire({
//                         icon: 'success',
//                         title: 'Success!',
//                         text: response.message || 'Your form has been submitted successfully!',
//                         showConfirmButton: false,
//                     });

//                     // if (response.url) {
//                     //     window.location.href = response.url; // send user to external/internal page
//                     // }
//                     if (response.download) {
//                         fetch(response.download)
//                             .then(res => res.blob())
//                             .then(blob => {
//                                 const url = window.URL.createObjectURL(blob);
//                                 const a = document.createElement('a');
//                                 a.href = url;
//                                 a.download = `${response.fileName}.pdf`; // file name set karo
//                                 document.body.appendChild(a);
//                                 a.click();
//                                 a.remove();
//                             })
//                             .catch(() => {
//                                 Swal.fire({
//                                     icon: 'error',
//                                     title: 'Download Failed',
//                                     text: 'There was an issue downloading your file. Please try again later.',
//                                     showConfirmButton: false,
//                                 });
//                             });
//                     }
//                     // window.location.href = response.url;





//                     $(formSelector)[0].reset();
//                     $(formSelector).find('.nice-select').each(function () {
//                         var $this = $(this);
//                         var originalSelect = $this.prev('select');
//                         originalSelect.val('');
//                         $this.niceSelect('update');
//                     });
//                 } else {
//                     Swal.fire({
//                         icon: 'error',
//                         title: 'Oops...',
//                         text: response.message || 'Something went wrong. Please try again.',
//                         showConfirmButton: false,
//                     });
//                 }
//             },
//             error: function (xhr, status, error) {
//                 var response = xhr.responseJSON;

//                 if (response.status === "error" && response.errors) {
//                     var errorMessages = "";
//                     $.each(response.errors, function (field, messages) {
//                         errorMessages += messages.join(", ") + "\n";
//                     });
//                     Swal.fire({
//                         icon: 'error',
//                         title: 'Validation Errors',
//                         text: errorMessages || 'There are some errors in the form. Please check and try again.',
//                         showConfirmButton: false,
//                     });
//                 } else {
//                     Swal.fire({
//                         icon: 'error',
//                         title: 'Error!',
//                         text: 'An error occurred while submitting your form. Please try again.',
//                         showConfirmButton: false,
//                     });
//                 }
//             }
//         });
//     });
// }






const FormHandler = (() => {
    const alert = (icon, title, text) =>
        Swal.fire({ icon, title, text, timer: 3000, showConfirmButton: false, timerProgressBar: true });

    const download = async (url, fileName) => {
        try {
            const blob = await fetch(url).then(r => r.blob());
            const a = Object.assign(document.createElement('a'), {
                href: URL.createObjectURL(blob),
                download: `${fileName}.pdf`
            });
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch {
            alert('error', 'Download Failed', 'Could not download the file. Please try again.');
        }
    };

    const init = (selector) => {
        $(document).on('submit', selector, async function (e) {
            e.preventDefault();
            const $form = $(this);
            if (!validateForm($form)) {
                Swal.fire({
                    icon: 'error',
                    title: 'Missing Required Information',
                    text: 'Please ensure all required fields are filled in before submitting.',
                    showConfirmButton: false,
                });
                return;
            }

            Swal.fire({
                title: 'Processing...',
                text: 'Please wait while we submit your form.',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            $.ajax({
                url: $form.attr('action'),
                type: 'POST',
                data: $form.serialize(),
                success: async (res) => {
                    // console.log(res);
                    // return
                    // await alert('success', 'Success!', res.message);
                    if (res.download) await download(res.download, res.fileName);
                    $form[0].reset();
                    $form.find('.nice-select').each(function () {
                        $(this).prev('select').val('');
                        $(this).niceSelect('update');
                    });
                    await alert('success', 'Success!', res.message);
                    window.location.href = res.url;
                },
                error: (xhr) => {
                    const res = xhr.responseJSON;

                    if (res?.errors) {
                        var errorMessages = "";
                        $.each(res.errors, function (field, messages) {
                            errorMessages += messages.join(", ") + "\n";
                        });
                        Swal.fire({
                            icon: 'error',
                            title: 'Validation Errors',
                            text: errorMessages || 'There are some errors in the form. Please check and try again.',
                            showConfirmButton: false,
                        });
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error!',
                            text: res?.message || 'An error occurred while submitting your form. Please try again.',
                            showConfirmButton: false,
                        });
                    }
                }
            });
        });
    };

    return { init };
})();

// Usage
$(function () {

    FormHandler.init('#service-form');
    FormHandler.init('#inquiry-form');
    FormHandler.init('#modal-form');
    FormHandler.init('#banner-form');
    FormHandler.init('#contact-form');
    FormHandler.init('#order-form');


});










// function validateForm(formSelector) {
//     var isValid = true;
//     $(formSelector).find('input, select, textarea').each(function () {
//         var $this = $(this);
//         var type = $this.attr('type');
//         var name = $this.attr('name');
//         var optional = $this.data('optional');

//         if ($this.is(':visible')) {
//             if (optional && !$this.val()) {
//                 $this.css('border', '');
//                 return true; // continue to next field
//             }
//             if (type === 'radio') {
//                 if ($('input[name="' + name + '"]:checked').length === 0) {
//                     isValid = false;
//                     $this.closest('.form-group').css('border', '1px solid red');
//                 } else {
//                     $this.closest('.form-group').css('border', '');
//                 }
//             }
//             else if (type === 'checkbox') {
//                 if (!$this.is(':checked')) {
//                     isValid = false;
//                     $this.closest('.form-check').css('border', '1px solid red');
//                 } else {
//                     $this.closest('.form-check').css('border', '');
//                 }
//             }
//             else if ($this.is('select')) {
//                 if ($this.val() === null || $this.val() === '') {
//                     isValid = false;

//                     // For Select2, add border to the container
//                     var select2Container = $this.next('.select2-container');
//                     select2Container.css('border', '1px solid red');
//                 } else {
//                     var select2Container = $this.next('.select2-container');
//                     select2Container.css('border', '');
//                 }
//             }
//             else if ($this.val() === '') {
//                 isValid = false;
//                 $this.css('border', '1px solid red');
//             } else {
//                 $this.css('border', '');
//             }
//         }
//     });
//     return isValid;
// }


function validateForm(formSelector) {
    var isValid = true;
    var checkedGroups = {};

    $(formSelector).find('input, select, textarea').each(function () {
        var $this = $(this);
        var type = $this.attr('type');
        var name = $this.attr('name');
        var optional = $this.data('optional');
        if (!$this.is(':visible')) return true;
        if (optional && !$this.val()) {
            $this.css('border', '');
            return true;
        }
        if (type === 'radio') {
            if ($('input[name="' + name + '"]:checked').length === 0) {
                isValid = false;
                $this.closest('.form-group').css('border', '1px solid red');
            } else {
                $this.closest('.form-group').css('border', '');
            }
        }
        // else if (type === 'checkbox') {

        //     if (checkedGroups[name]) return true;
        //     checkedGroups[name] = true;

        //     if ($('input[name="' + name + '"]:checked').length !== 1) {
        //         isValid = false;
        //         $('input[name="' + name + '"]').closest('.form-check')
        //             .css('border', '1px solid red');
        //     } else {
        //         $('input[name="' + name + '"]').closest('.form-check')
        //             .css('border', '');
        //     }
        // }
        else if ($this.is('select')) {
            var select2Container = $this.next('.select2-container');

            if (!$this.val()) {
                isValid = false;
                select2Container.css('border', '1px solid red');
            } else {
                select2Container.css('border', '');
            }
        }
        else if (!$this.val()) {
            isValid = false;
            $this.css('border', '1px solid red');
        } else {
            $this.css('border', '');
        }
    });
    return isValid;
}





// $(function () {
//     handleFormSubmission("#service-form");
//     handleFormSubmission("#inquiry-form");
//     handleFormSubmission("#modal-form");
//     handleFormSubmission("#banner-form");
//     handleFormSubmission("#contact-form");
//     handleFormSubmission("#order-form");
// });
