/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
function changeShop() {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = window.ShuupAdminConfig.browserUrls.setShop;
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "shop";
    input.id = "shop";
    input.value = $(this).val();
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
}

$(function(){
    "use strict";
    $("select.shop-changer").change(changeShop);
});
