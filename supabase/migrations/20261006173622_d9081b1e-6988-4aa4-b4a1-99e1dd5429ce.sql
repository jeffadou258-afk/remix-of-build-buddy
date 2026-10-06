DO $$
DECLARE _uid uuid := 'ca2da636-0bf9-4094-914a-936571988664';
BEGIN
  IF EXISTS (SELECT 1 FROM public.user_roles WHERE role = 'admin') THEN
    RAISE EXCEPTION 'bootstrap refusé : un administrateur existe déjà';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = _uid AND lower(email) = 'jeffadou258@gmail.com') THEN
    RAISE EXCEPTION 'bootstrap refusé : compte cible introuvable';
  END IF;
  INSERT INTO public.user_roles (user_id, role, granted_by) VALUES (_uid, 'admin', NULL);
  INSERT INTO public.admin_audit_log (actor_id, actor_roles, action, permission, target_type, target_id, reason, result, before, after)
  VALUES (_uid, '{}', 'roles.bootstrap_first_admin', 'roles.manage', 'user', _uid::text,
          'Bootstrap du premier administrateur (approuvé par le propriétaire)', 'allowed', '[]'::jsonb, '["admin"]'::jsonb);
END $$;